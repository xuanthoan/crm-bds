from datetime import datetime
from uuid import UUID
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

def _list(db, page, page_size, **f):
    q = db.query(AuditLog)
    if f.get('date_from'): q = q.filter(AuditLog.created_at >= f['date_from'])
    if f.get('date_to'): q = q.filter(AuditLog.created_at <= f['date_to'])
    for key, col in [('actor_id', AuditLog.actor_id), ('module', AuditLog.module), ('entity_type', AuditLog.entity_type), ('entity_id', AuditLog.entity_id), ('action', AuditLog.action)]:
        if f.get(key): q = q.filter(col == f[key])
    if f.get('q'):
        term = f"%{f['q'].strip()}%"
        q = q.filter(or_(AuditLog.actor_name.ilike(term), AuditLog.actor_email.ilike(term), AuditLog.module.ilike(term), AuditLog.entity_type.ilike(term), AuditLog.entity_id.ilike(term), AuditLog.entity_label.ilike(term), AuditLog.action.ilike(term), AuditLog.description.ilike(term), AuditLog.reason.ilike(term)))
    total = q.count()
    items = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {'items': [audit_log_to_dict(i, db) for i in items], 'total': total, 'page': page, 'page_size': page_size}

@router.get('')
def list_audit_logs(page:int=Query(1,ge=1), page_size:int=Query(20,ge=1,le=100), date_from:datetime|None=None, date_to:datetime|None=None, actor_id:UUID|None=None, module:str|None=None, entity_type:str|None=None, entity_id:str|None=None, action:str|None=None, q:str|None=None, db:Session=Depends(get_db), actor:User=Depends(need)):
    return success_response(_list(db, page, page_size, date_from=date_from, date_to=date_to, actor_id=actor_id, module=module, entity_type=entity_type, entity_id=entity_id, action=action, q=q))

@router.get('/entity/{entity_type}/{entity_id}')
def entity_timeline(entity_type:str, entity_id:str, page:int=Query(1,ge=1), page_size:int=Query(20,ge=1,le=100), db:Session=Depends(get_db), actor:User=Depends(need)):
    return success_response(_list(db, page, page_size, entity_type=entity_type, entity_id=entity_id))

@router.get('/{id}')
def audit_detail(id:UUID, db:Session=Depends(get_db), actor:User=Depends(need)):
    log = db.query(AuditLog).filter(AuditLog.id == id).first()
    if not log: raise HTTPException(404, 'Không tìm thấy lịch sử thao tác.')
    return success_response(audit_log_to_dict(log, db))
