import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow() -> datetime: return datetime.now(timezone.utc)

class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_bookings_property_status", "property_unit_id", "status"),
        Index("ix_bookings_assigned_status", "assigned_user_id", "status"),
        Index("ix_bookings_customer_status", "customer_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True, nullable=False)
    property_unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("property_units.id"), index=True, nullable=False)
    source_lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"), index=True)
    source_deal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("deals.id"), index=True)
    assigned_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True, nullable=False)
    booking_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2)); deposit_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2)); refund_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    booking_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True); reservation_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True); deposit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(Text); refund_reason: Mapped[str | None] = mapped_column(Text); note: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False); updated_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id")); deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False); deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    customer = relationship("Customer", back_populates="bookings", lazy="joined"); property_unit = relationship("PropertyUnit", back_populates="bookings", lazy="joined")
    source_lead = relationship("Lead", lazy="joined"); source_deal = relationship("Deal", foreign_keys=[source_deal_id], lazy="joined")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id], lazy="joined"); creator = relationship("User", foreign_keys=[created_by_id], lazy="joined"); updater = relationship("User", foreign_keys=[updated_by_id], lazy="joined"); deleter = relationship("User", foreign_keys=[deleted_by_id], lazy="joined")
    deals = relationship("Deal", foreign_keys="Deal.booking_id", back_populates="booking", lazy="select")
    contracts = relationship("Contract", back_populates="booking", lazy="select")
    activities = relationship("BookingActivity", back_populates="booking", order_by="BookingActivity.created_at.desc()", cascade="all, delete-orphan")
