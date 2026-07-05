from datetime import datetime
from uuid import UUID
import unicodedata
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.permissions.dependencies import require_auth, user_has_permission
from app.services.audit_log_service import audit_log_to_dict

router = APIRouter(prefix='/audit-logs', tags=['audit-logs'])

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

def _matches_enriched_keyword(row: dict, keyword: str) -> bool:
    normalized_keyword = _normalize_search_text(keyword)
    if not normalized_keyword:
        return True
    fields = [
        row.get('actor_name'), row.get('actor_email'), row.get('actor_id'),
        row.get('module'), row.get('module_label'), row.get('_raw_module'),
        row.get('action'), row.get('action_label'), row.get('_raw_action'),
        row.get('entity_type'), row.get('entity_id'), row.get('entity_label'), row.get('entity_display'), row.get('_raw_entity_label'),
        row.get('description'), row.get('reason'),
    ]
    haystack = ' '.join(_normalize_search_text(v) for v in fields if v is not None)
    return normalized_keyword in haystack

def _apply_actor_filter(q, value: str | None):
    if not value:
        return q
    text = str(value).strip()
    try:
        actor_uuid = UUID(text)
        return q.filter(or_(AuditLog.actor_id == actor_uuid, AuditLog.user_id == actor_uuid))
    except (TypeError, ValueError):
        term = f'%{text}%'
        return q.filter(or_(AuditLog.actor_name.ilike(term), AuditLog.actor_email.ilike(term)))

def _list(db, page, page_size, **f):
    q = db.query(AuditLog)
    if f.get('date_from'): q = q.filter(AuditLog.created_at >= f['date_from'])
    if f.get('date_to'): q = q.filter(AuditLog.created_at <= f['date_to'])
    q = _apply_actor_filter(q, f.get('actor_id'))
    for key, col in [('module', AuditLog.module), ('entity_type', AuditLog.entity_type), ('entity_id', AuditLog.entity_id), ('action', AuditLog.action)]:
        if f.get(key): q = q.filter(col == f[key])
    q = q.order_by(AuditLog.created_at.desc())
    keyword = (f.get('q') or '').strip()
    if keyword:
        rows = []
        for log in q.all():
            row = audit_log_to_dict(log, db)
            row['_raw_module'] = log.module
            row['_raw_action'] = log.action
            row['_raw_entity_label'] = log.entity_label
            rows.append(row)
        matched = [row for row in rows if _matches_enriched_keyword(row, keyword)]
        total = len(matched)
        start = (page - 1) * page_size
        return {'items': matched[start:start + page_size], 'total': total, 'page': page, 'page_size': page_size}
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {'items': [audit_log_to_dict(i, db) for i in items], 'total': total, 'page': page, 'page_size': page_size}

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
