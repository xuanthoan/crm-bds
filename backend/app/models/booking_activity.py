import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow() -> datetime: return datetime.now(timezone.utc)
class BookingActivity(Base):
    __tablename__ = "booking_activities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), index=True, nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(30), index=True, nullable=False); title: Mapped[str] = mapped_column(String(255), nullable=False); content: Mapped[str | None] = mapped_column(Text); old_value: Mapped[str | None] = mapped_column(Text); new_value: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
    booking = relationship("Booking", back_populates="activities"); actor = relationship("User", lazy="joined")
