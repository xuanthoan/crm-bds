import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow(): return datetime.now(timezone.utc)

class TaskAssignee(Base):
    __tablename__ = "task_assignees"
    __table_args__ = (UniqueConstraint("task_id", "user_id", name="uq_task_assignees_task_user"), Index("ix_task_assignees_task_id", "task_id"), Index("ix_task_assignees_user_id", "user_id"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    task = relationship("Task", back_populates="task_assignees")
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")

class TaskWatcher(Base):
    __tablename__ = "task_watchers"
    __table_args__ = (UniqueConstraint("task_id", "user_id", name="uq_task_watchers_task_user"), Index("ix_task_watchers_task_id", "task_id"), Index("ix_task_watchers_user_id", "user_id"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    task = relationship("Task", back_populates="task_watchers")
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")

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
    assigned_user = relationship("User", foreign_keys=[assigned_user_id], lazy="selectin")
    creator = relationship("User", foreign_keys=[created_by_id], lazy="selectin")
    related_customer = relationship("Customer", lazy="selectin")
    related_lead = relationship("Lead", lazy="selectin")
    related_booking = relationship("Booking", lazy="selectin")
    related_deal = relationship("Deal", lazy="selectin")
    related_contract = relationship("Contract", lazy="selectin")
    related_property_unit = relationship("PropertyUnit", lazy="selectin")
    activities = relationship("TaskActivity", back_populates="task", order_by="TaskActivity.created_at.desc()", cascade="all, delete-orphan")
    task_assignees = relationship("TaskAssignee", back_populates="task", cascade="all, delete-orphan", lazy="selectin")
    task_watchers = relationship("TaskWatcher", back_populates="task", cascade="all, delete-orphan", lazy="selectin")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan", lazy="selectin")
    related_links = relationship("TaskRelatedLink", back_populates="task", cascade="all, delete-orphan", lazy="selectin")
