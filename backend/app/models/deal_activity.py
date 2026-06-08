import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow() -> datetime: return datetime.now(timezone.utc)

class DealActivity(Base):
    __tablename__ = "deal_activities"
    __table_args__ = (Index("ix_deal_activities_deal_created_at", "deal_id", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False); title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text); old_value: Mapped[str | None] = mapped_column(Text); new_value: Mapped[str | None] = mapped_column(Text); metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
    deal = relationship("Deal", back_populates="activities"); user = relationship("User", lazy="joined")
