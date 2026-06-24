import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow(): return datetime.now(timezone.utc)

class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (Index("ix_tasks_assigned_user_id", "assigned_user_id"), Index("ix_tasks_due_at", "due_at"), Index("ix_tasks_status", "status"), Index("ix_tasks_source_booking", "source_event", "related_booking_id"), Index("ix_tasks_source_contract", "source_event", "related_contract_id"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(40), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    related_customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    related_lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"))
    related_booking_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id"))
    related_deal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("deals.id"))
    related_contract_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id"))
    related_property_unit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("property_units.id"))
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_event: Mapped[str | None] = mapped_column(String(80))
    note: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    assigned_user = relationship("User", foreign_keys=[assigned_user_id], lazy="joined")
    creator = relationship("User", foreign_keys=[created_by_id], lazy="joined")
    related_customer = relationship("Customer", lazy="joined")
    related_lead = relationship("Lead", lazy="joined")
    related_booking = relationship("Booking", lazy="joined")
    related_deal = relationship("Deal", lazy="joined")
    related_contract = relationship("Contract", lazy="joined")
    related_property_unit = relationship("PropertyUnit", lazy="joined")
    activities = relationship("TaskActivity", back_populates="task", order_by="TaskActivity.created_at.desc()", cascade="all, delete-orphan")
