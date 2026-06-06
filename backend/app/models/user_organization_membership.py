import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class UserOrganizationMembership(Base):
    __tablename__ = "user_organization_memberships"
    __table_args__ = (UniqueConstraint("user_id", "department_id", "team_id", name="uq_user_organization_membership"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), index=True, nullable=True)
    team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), index=True, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    position_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    user = relationship("User", lazy="joined")
    department = relationship("Department", back_populates="memberships", lazy="joined")
    team = relationship("Team", back_populates="memberships", lazy="joined")
