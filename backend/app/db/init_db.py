from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User, UserStatus
from app.permissions.constants import DEFAULT_ROLES, PERMISSION_CODES, ROLE_PERMISSION_CODES, permission_module, permission_name


def seed_permissions(db: Session) -> dict[str, Permission]:
    permissions_by_code = {permission.code: permission for permission in db.scalars(select(Permission)).all()}
    for code in PERMISSION_CODES:
        if code not in permissions_by_code:
            permission = Permission(code=code, name=permission_name(code), module=permission_module(code))
            db.add(permission)
            permissions_by_code[code] = permission
    db.flush()
    return permissions_by_code


def seed_roles(db: Session, permissions_by_code: dict[str, Permission]) -> dict[str, Role]:
    roles_by_code = {role.code: role for role in db.scalars(select(Role)).all()}
    for role_data in DEFAULT_ROLES:
        role = roles_by_code.get(role_data["code"])
        if role is None:
            role = Role(name=role_data["name"], code=role_data["code"], is_system=True)
            db.add(role)
            roles_by_code[role.code] = role
        else:
            role.name = role_data["name"]
            role.is_system = True
    db.flush()

    for role_code, permission_codes in ROLE_PERMISSION_CODES.items():
        role = roles_by_code[role_code]
        role.permissions = [permissions_by_code[code] for code in permission_codes]
    db.flush()
    return roles_by_code


def seed_default_admin(db: Session, roles_by_code: dict[str, Role]) -> None:
    admin = db.scalar(select(User).where(User.email == settings.default_admin_email.lower()))
    admin_role = roles_by_code["admin"]
    if admin is None:
        admin = User(
            email=settings.default_admin_email.lower(),
            full_name=settings.default_admin_name,
            hashed_password=get_password_hash(settings.default_admin_password),
            status=UserStatus.ACTIVE.value,
            is_superuser=True,
            roles=[admin_role],
        )
        db.add(admin)
    else:
        admin.full_name = admin.full_name or settings.default_admin_name
        admin.status = UserStatus.ACTIVE.value
        admin.is_superuser = True
        if admin_role not in admin.roles:
            admin.roles.append(admin_role)
    db.flush()


def init_db(db: Session) -> None:
    permissions_by_code = seed_permissions(db)
    roles_by_code = seed_roles(db, permissions_by_code)
    seed_default_admin(db, roles_by_code)
    db.commit()
