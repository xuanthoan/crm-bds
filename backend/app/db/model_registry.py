"""Import all SQLAlchemy models so Alembic can discover Base.metadata.

Runtime model modules import Base from app.db.base. Keeping this aggregation in a
separate module avoids the circular import caused by importing models inside
app.db.base while those same models are still importing Base.
"""

from app.models.audit_log import AuditLog  # noqa: F401
from app.models.permission import Permission  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.role import Role, role_permissions  # noqa: F401
from app.models.user import User, user_roles  # noqa: F401
