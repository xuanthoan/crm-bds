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
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_primary: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    phone_secondary: Mapped[str | None] = mapped_column(String(50), index=True)
    zalo: Mapped[str | None] = mapped_column(String(255))
    facebook: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(80), index=True)
    project_interest: Mapped[str | None] = mapped_column(String(255))
    location_interest: Mapped[str | None] = mapped_column(String(255))
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    bedroom_need: Mapped[int | None] = mapped_column(Integer)
    area_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    area_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="new", index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    converted_customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    lost_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    owner = relationship("User", foreign_keys=[owner_id], lazy="selectin")
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="selectin")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id], lazy="selectin")
    activities = relationship("LeadActivity", back_populates="lead", lazy="selectin", cascade="all, delete-orphan")
