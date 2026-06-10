import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow() -> datetime: return datetime.now(timezone.utc)
class PropertyStatusHistory(Base):
    __tablename__ = "property_status_history"
    __table_args__ = (Index("ix_property_status_history_property_created", "property_unit_id", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("property_units.id", ondelete="CASCADE"), index=True, nullable=False)
    changed_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(30)); new_status: Mapped[str] = mapped_column(String(30), index=True, nullable=False); note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
    property_unit = relationship("PropertyUnit", back_populates="status_history"); changed_by = relationship("User", lazy="joined")
