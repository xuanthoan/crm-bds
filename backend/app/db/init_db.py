from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.permissions.constants import DEFAULT_ROLES, PERMISSION_CODES_BY_MODULE, ROLE_PERMISSION_MAP


def _permission_name(code: str) -> str:
    return code.replace("_", " ").replace(".", " · ").title()


def seed_roles_permissions(db: Session) -> None:
    role_by_code: dict[str, Role] = {}
    for role_data in DEFAULT_ROLES:
        role = db.scalar(select(Role).where(Role.code == role_data["code"]))
        if not role:
            role = Role(**role_data, is_system=True)
            db.add(role)
            db.flush()
        role_by_code[role.code] = role

    permission_by_code: dict[str, Permission] = {}
    for module, codes in PERMISSION_CODES_BY_MODULE.items():
        for code in codes:
            permission = db.scalar(select(Permission).where(Permission.code == code))
            if not permission:
                permission = Permission(name=_permission_name(code), code=code, module=module)
                db.add(permission)
                db.flush()
            permission_by_code[permission.code] = permission

    for role_code, permission_codes in ROLE_PERMISSION_MAP.items():
        role = role_by_code[role_code]
        desired_permissions = [permission_by_code[code] for code in permission_codes]
        desired_codes = set(permission_codes)
        # Sprint 8 replaces the legacy deal permission vocabulary. Keep system roles
        # synchronized so obsolete deal grants do not survive an application upgrade.
        for permission in list(role.permissions):
            if permission.module in {"deals", "inventory"} and permission.code not in desired_codes:
                role.permissions.remove(permission)
        existing_codes = {permission.code for permission in role.permissions}
        for permission in desired_permissions:
            if permission.code not in existing_codes:
                role.permissions.append(permission)


def seed_default_admin(db: Session) -> None:
    settings = get_settings()
    admin_role = db.scalar(select(Role).where(Role.code == "admin"))
    admin = db.scalar(select(User).where(User.email == settings.default_admin_email.lower()))
    if not admin:
        admin = User(
            email=settings.default_admin_email.lower(),
            full_name=settings.default_admin_name,
            hashed_password=get_password_hash(settings.default_admin_password),
            status="active",
            is_superuser=True,
        )
        db.add(admin)
        db.flush()
    else:
        admin.status = "active"
        admin.is_superuser = True
    if admin_role and admin_role not in admin.roles:
        admin.roles.append(admin_role)

DEMO_SALE_USERS = [
    {"email": "sale04@gmail.com", "full_name": "Sale 04"},
    {"email": "sale05@gmail.com", "full_name": "Sale 05"},
    {"email": "sale7@gmail.com", "full_name": "Sale 7"},
    {"email": "sale06@gmail.com", "full_name": "Sale06"},
    {"email": "sale01@test.com", "full_name": "Sale Test"},
]


def seed_demo_users(db: Session) -> None:
    settings = get_settings()
    if not settings.seed_demo_users:
        return
    sale_role = db.scalar(select(Role).where(Role.code == "sale"))
    if not sale_role:
        return
    password_hash = get_password_hash(settings.demo_user_password)
    for item in DEMO_SALE_USERS:
        email = item["email"].lower()
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                email=email,
                full_name=item["full_name"],
                hashed_password=password_hash,
                status="active",
                is_superuser=False,
            )
            db.add(user)
            db.flush()
        elif user.deleted_at is None:
            user.status = "active"
        if user.deleted_at is None and sale_role not in user.roles:
            user.roles.append(sale_role)


def init_db(db: Session) -> None:
    seed_roles_permissions(db)
    seed_default_admin(db)
    seed_demo_users(db)
    db.commit()
