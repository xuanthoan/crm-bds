import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow(): return datetime.now(timezone.utc)

class LeadTask(Base):
    __tablename__ = "lead_tasks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"), index=True)
    title: Mapped[str] = mapped_column(String(255)); description: Mapped[str | None] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(30)); status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True); due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_to_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    completed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True); reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    result_note: Mapped[str | None] = mapped_column(Text); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow); deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    lead = relationship("Lead", back_populates="tasks"); assigned_to = relationship("User", foreign_keys=[assigned_to_id], lazy="joined")
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined"); completed_by = relationship("User", foreign_keys=[completed_by_id], lazy="joined")
