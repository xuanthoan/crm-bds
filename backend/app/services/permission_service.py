from collections import defaultdict

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.permission import Permission


def serialize_permission(permission: Permission) -> dict:
    return {
        "id": permission.id,
        "name": permission.name,
        "code": permission.code,
        "module": permission.module,
        "description": permission.description,
        "created_at": permission.created_at,
        "updated_at": permission.updated_at,
    }


def list_permissions_grouped(db: Session, *, module: str | None = None, search: str | None = None) -> list[dict]:
    query = select(Permission)
    if module:
        query = query.where(Permission.module == module)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(or_(Permission.code.ilike(term), Permission.name.ilike(term), Permission.description.ilike(term)))
    permissions = list(db.scalars(query.order_by(Permission.module, Permission.code)).all())
    grouped: dict[str, list[dict]] = defaultdict(list)
    for permission in permissions:
        grouped[permission.module].append(serialize_permission(permission))
    return [{"module": module_name, "permissions": items} for module_name, items in grouped.items()]
