from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.audit_log import AuditLog  # noqa: E402,F401
from app.models.permission import Permission  # noqa: E402,F401
from app.models.refresh_token import RefreshToken  # noqa: E402,F401
from app.models.role import Role, role_permissions  # noqa: E402,F401
from app.models.user import User, user_roles  # noqa: E402,F401
