import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_primary: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    phone_secondary: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    zalo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    project_interest: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_interest: Mapped[str | None] = mapped_column(String(255), nullable=True)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    bedroom_need: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    area_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), index=True, default="new", nullable=False)
    priority: Mapped[str] = mapped_column(String(30), default="medium", nullable=False)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    converted_customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    converted_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    lost_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    owner = relationship("User", foreign_keys=[owner_id], lazy="joined")
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id], lazy="joined")
    converted_by = relationship("User", foreign_keys=[converted_by_id], lazy="joined")
    converted_customer = relationship("Customer", foreign_keys=[converted_customer_id], lazy="joined")
    source_customer = relationship("Customer", foreign_keys="Customer.source_lead_id", back_populates="source_lead", uselist=False)
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan", order_by="LeadActivity.created_at.desc()")
    tasks = relationship("LeadTask", back_populates="lead", order_by="LeadTask.due_at.desc()")
    appointments = relationship("LeadAppointment", back_populates="lead", order_by="LeadAppointment.start_at.desc()")
