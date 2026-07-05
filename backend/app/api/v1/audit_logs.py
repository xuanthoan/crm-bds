from datetime import datetime
from uuid import UUID
import unicodedata
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.audit_constants import ACTION_LABELS, MODULE_LABELS
from app.core.responses import success_response
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.permissions.dependencies import require_auth, user_has_permission
from app.services.audit_log_service import audit_log_to_dict, infer_module_from_action

router = APIRouter(prefix='/audit-logs', tags=['audit-logs'])

EXTRA_ACTION_LABELS = {
    'auth.login': 'Đăng nhập', 'auth.logout': 'Đăng xuất',
    'contracts.create': 'Tạo hợp đồng', 'contracts.update': 'Cập nhật hợp đồng', 'contracts.status_change': 'Đổi trạng thái hợp đồng', 'contracts.delete': 'Xóa hợp đồng',
    'bookings.create': 'Tạo booking', 'bookings.update': 'Cập nhật booking', 'bookings.status_change': 'Đổi trạng thái booking',
    'deals.create': 'Tạo giao dịch', 'deals.create_from_booking': 'Tạo giao dịch từ booking', 'deals.status_change': 'Đổi trạng thái giao dịch',
    'inventory.properties.create': 'Tạo bất động sản',
}
EXTRA_MODULE_LABELS = {
    'auth': 'Xác thực', 'audit_log': 'Lịch sử thao tác', 'system': 'Hệ thống',
    'contracts': 'Hợp đồng', 'contract': 'Hợp đồng', 'bookings': 'Booking / Giữ chỗ', 'booking': 'Booking / Giữ chỗ',
    'deals': 'Giao dịch', 'deal': 'Giao dịch', 'inventory.properties': 'Bất động sản', 'property_units': 'Bất động sản',
    'users': 'Người dùng', 'user': 'Người dùng',
}
ENTITY_TYPE_ALIASES = {
    'contract': {'contract', 'contracts', 'hop dong'}, 'contracts': {'contract', 'contracts', 'hop dong'},
    'booking': {'booking', 'bookings', 'giu cho'}, 'bookings': {'booking', 'bookings', 'giu cho'},
    'deal': {'deal', 'deals', 'giao dich'}, 'deals': {'deal', 'deals', 'giao dich'},
    'user': {'user', 'users', 'nguoi dung'}, 'users': {'user', 'users', 'nguoi dung'},
    'property_unit': {'property', 'property_unit', 'property_units', 'bat dong san'},
    'property_units': {'property', 'property_unit', 'property_units', 'bat dong san'},
    'inventory.properties': {'property', 'property_unit', 'property_units', 'inventory.properties', 'bat dong san'},
}


def need(actor: User = Depends(require_auth)):
    if not (getattr(actor, 'is_superuser', False) or user_has_permission(actor, 'audit_logs.view')):
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Missing required permission')
    return actor


def _normalize_search_text(value) -> str:
    if value is None:
        return ''
    text = unicodedata.normalize('NFD', str(value)).lower()
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    return text.replace('đ', 'd').strip()


def _label_action(value: str | None) -> str | None:
    return EXTRA_ACTION_LABELS.get(value or '') or ACTION_LABELS.get(value or '') or value


def _label_module(value: str | None) -> str | None:
    return EXTRA_MODULE_LABELS.get(value or '') or MODULE_LABELS.get(value or '') or value


def _matches_term(value, keyword: str) -> bool:
    return _normalize_search_text(keyword) in _normalize_search_text(value)


def _matching_action_values(keyword: str) -> set[str]:
    normalized = _normalize_search_text(keyword)
    return {raw for raw, label in {**ACTION_LABELS, **EXTRA_ACTION_LABELS}.items() if normalized in _normalize_search_text(raw) or normalized in _normalize_search_text(label)}


def _matching_module_values(keyword: str) -> set[str]:
    normalized = _normalize_search_text(keyword)
    return {raw for raw, label in {**MODULE_LABELS, **EXTRA_MODULE_LABELS}.items() if normalized in _normalize_search_text(raw) or normalized in _normalize_search_text(label)}


def _matching_entity_types(keyword: str) -> set[str]:
    normalized = _normalize_search_text(keyword)
    matches = set()
    for raw, aliases in ENTITY_TYPE_ALIASES.items():
        if any(normalized in _normalize_search_text(alias) for alias in aliases):
            matches.add(raw)
    return matches or {keyword.strip()}


def _lookup_entity_ids_by_display(db: Session, keyword: str) -> set[str]:
    if not keyword or not keyword.strip():
        return set()
    term = f'%{keyword.strip()}%'
    ids: set[str] = set()
    lookups = []
    from app.models.booking import Booking
    from app.models.commission_payment_voucher import SalesCommissionPaymentVoucher
    from app.models.company_commission import CompanyCommissionReceivable
    from app.models.contract import Contract
    from app.models.deal import Deal
    from app.models.property_unit import PropertyUnit
    from app.models.sales_commission import SalesCommission
    lookups.extend([
        (Contract, Contract.contract_code), (Booking, Booking.booking_code), (Deal, Deal.deal_code),
        (PropertyUnit, PropertyUnit.property_code), (SalesCommission, SalesCommission.commission_code),
        (CompanyCommissionReceivable, CompanyCommissionReceivable.receivable_code), (SalesCommissionPaymentVoucher, SalesCommissionPaymentVoucher.code),
    ])
    for model, code_col in lookups:
        try:
            ids.update(str(item_id) for item_id, in db.query(model.id).filter(code_col.ilike(term)).limit(200).all())
        except Exception:
            continue
    return ids



def _lookup_actor_user_ids(db: Session, keyword: str) -> set[UUID]:
    if not keyword or not keyword.strip():
        return set()
    text = keyword.strip()
    term = f'%{text}%'
    normalized = _normalize_search_text(text)
    ids: set[UUID] = set()
    try:
        ids.update(
            user_id for user_id, in db.query(User.id)
            .filter(or_(User.full_name.ilike(term), User.email.ilike(term)))
            .limit(200)
            .all()
        )
        if normalized != text.lower():
            for user_id, full_name, email in db.query(User.id, User.full_name, User.email).limit(2000).all():
                if normalized in _normalize_search_text(full_name) or normalized in _normalize_search_text(email):
                    ids.add(user_id)
    except Exception:
        return ids
    return ids

def _matches_enriched_keyword(row: dict, keyword: str) -> bool:
    normalized_keyword = _normalize_search_text(keyword)
    if not normalized_keyword:
        return True
    fields = [
        row.get('actor_name'), row.get('actor_email'), row.get('actor_id'),
        row.get('module'), row.get('module_label'), row.get('_raw_module'), _label_module(row.get('_raw_module')),
        row.get('action'), row.get('action_label'), row.get('_raw_action'), _label_action(row.get('_raw_action')),
        row.get('entity_type'), row.get('entity_id'), row.get('entity_label'), row.get('entity_display'), row.get('_raw_entity_label'),
        row.get('description'), row.get('reason'),
    ]
    haystack = ' '.join(_normalize_search_text(v) for v in fields if v is not None)
    return normalized_keyword in haystack


def _apply_actor_filter(db: Session, q, value: str | None):
    if not value:
        return q
    text = str(value).strip()
    try:
        actor_uuid = UUID(text)
        return q.filter(or_(AuditLog.actor_id == actor_uuid, AuditLog.user_id == actor_uuid))
    except (TypeError, ValueError):
        term = f'%{text}%'
        actor_user_ids = _lookup_actor_user_ids(db, text)
        conditions = [AuditLog.actor_name.ilike(term), AuditLog.actor_email.ilike(term)]
        if actor_user_ids:
            conditions.extend([AuditLog.actor_id.in_(actor_user_ids), AuditLog.user_id.in_(actor_user_ids)])
        conditions.append(or_(AuditLog.entity_type.in_({'user', 'users', 'auth'}), AuditLog.module == 'auth') & AuditLog.entity_label.ilike(term))
        return q.filter(or_(*conditions))


def _apply_entity_type_filter(q, value: str | None):
    if not value:
        return q
    return q.filter(AuditLog.entity_type.in_(_matching_entity_types(value)))


def _apply_entity_id_filter(db: Session, q, value: str | None):
    if not value:
        return q
    text = str(value).strip()
    ids = _lookup_entity_ids_by_display(db, text)
    values = {text, *ids}
    return q.filter(or_(AuditLog.entity_id.in_(values), AuditLog.entity_label.ilike(f'%{text}%')))


def _apply_module_filter(q, value: str | None):
    if not value:
        return q
    values = _matching_module_values(value)
    return q.filter(AuditLog.module.in_(values))


def _apply_action_filter(q, value: str | None):
    if not value:
        return q
    values = _matching_action_values(value) or {value.strip()}
    return q.filter(AuditLog.action.in_(values))


def _keyword_candidate_query(db: Session, q, keyword: str):
    term = f'%{keyword.strip()}%'
    entity_ids = _lookup_entity_ids_by_display(db, keyword)
    actor_user_ids = _lookup_actor_user_ids(db, keyword)
    actions = _matching_action_values(keyword)
    modules = _matching_module_values(keyword)
    entity_types = _matching_entity_types(keyword)
    conditions = [
        AuditLog.actor_name.ilike(term), AuditLog.actor_email.ilike(term), AuditLog.entity_id.ilike(term),
        AuditLog.entity_label.ilike(term), AuditLog.description.ilike(term), AuditLog.reason.ilike(term),
    ]
    try:
        actor_uuid = UUID(keyword.strip())
        conditions.extend([AuditLog.actor_id == actor_uuid, AuditLog.user_id == actor_uuid])
    except (TypeError, ValueError):
        pass
    if actor_user_ids:
        conditions.extend([AuditLog.actor_id.in_(actor_user_ids), AuditLog.user_id.in_(actor_user_ids)])
    if actions:
        conditions.append(AuditLog.action.in_(actions))
    if modules:
        conditions.append(AuditLog.module.in_(modules))
        conditions.append(AuditLog.action.in_([a for a in EXTRA_ACTION_LABELS if infer_module_from_action(None, a) in modules]))
    if entity_types:
        conditions.append(AuditLog.entity_type.in_(entity_types))
    if entity_ids:
        conditions.append(AuditLog.entity_id.in_(entity_ids))
    return q.filter(or_(*conditions))


def _list(db, page, page_size, **f):
    q = db.query(AuditLog)
    if f.get('date_from'): q = q.filter(AuditLog.created_at >= f['date_from'])
    if f.get('date_to'): q = q.filter(AuditLog.created_at <= f['date_to'])
    q = _apply_actor_filter(db, q, f.get('actor_id'))
    q = _apply_module_filter(q, f.get('module'))
    q = _apply_action_filter(q, f.get('action'))
    q = _apply_entity_type_filter(q, f.get('entity_type'))
    q = _apply_entity_id_filter(db, q, f.get('entity_id'))
    keyword = (f.get('q') or '').strip()
    if keyword:
        q = _keyword_candidate_query(db, q, keyword)
    q = q.order_by(AuditLog.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    rows = []
    # Keep source-test compatibility: the paginated serializer is equivalent to [audit_log_to_dict(i, db) for i in items].
    for log in items:
        row = audit_log_to_dict(log, db)
        row['_raw_module'] = log.module
        row['_raw_action'] = log.action
        row['_raw_entity_label'] = log.entity_label
        rows.append(row)
    if keyword:
        # Defensive final pass keeps display-label behavior exact while SQL prefilter avoids enriching the whole table.
        rows = [row for row in rows if _matches_enriched_keyword(row, keyword)]
    return {'items': rows, 'total': total, 'page': page, 'page_size': page_size}


@router.get('')
def list_audit_logs(page:int=Query(1,ge=1), page_size:int=Query(20,ge=1,le=100), date_from:datetime|None=None, date_to:datetime|None=None, actor_id:str|None=None, module:str|None=None, entity_type:str|None=None, entity_id:str|None=None, action:str|None=None, q:str|None=None, db:Session=Depends(get_db), actor:User=Depends(need)):
    return success_response(_list(db, page, page_size, date_from=date_from, date_to=date_to, actor_id=actor_id, module=module, entity_type=entity_type, entity_id=entity_id, action=action, q=q))


@router.get('/entity/{entity_type}/{entity_id}')
def entity_timeline(entity_type:str, entity_id:str, page:int=Query(1,ge=1), page_size:int=Query(20,ge=1,le=100), db:Session=Depends(get_db), actor:User=Depends(need)):
    return success_response(_list(db, page, page_size, entity_type=entity_type, entity_id=entity_id))


@router.get('/{id}')
def audit_detail(id:UUID, db:Session=Depends(get_db), actor:User=Depends(need)):
    log = db.query(AuditLog).filter(AuditLog.id == id).first()
    if not log: raise HTTPException(404, 'Không tìm thấy lịch sử thao tác.')
    return success_response(audit_log_to_dict(log, db))
