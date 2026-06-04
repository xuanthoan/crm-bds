from collections import defaultdict

from sqlalchemy import select
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
    }


def list_permissions_grouped(db: Session) -> list[dict]:
    permissions = list(db.scalars(select(Permission).order_by(Permission.module, Permission.code)).all())
    grouped: dict[str, list[dict]] = defaultdict(list)
    for permission in permissions:
        grouped[permission.module].append(serialize_permission(permission))
    return [{"module": module, "permissions": items} for module, items in grouped.items()]
