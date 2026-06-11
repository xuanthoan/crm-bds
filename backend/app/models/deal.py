import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow() -> datetime: return datetime.now(timezone.utc)

class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = (Index("ix_deals_owner_status", "owner_id", "status"), Index("ix_deals_pipeline_stage_status", "pipeline_stage", "status"), Index("ix_deals_customer_deleted_at", "customer_id", "deleted_at"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id"), index=True)
    property_unit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("property_units.id"), index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True, nullable=False)
    source_lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False); description: Mapped[str | None] = mapped_column(Text)
    deal_type: Mapped[str] = mapped_column(String(30), default="apartment", nullable=False)
    pipeline_stage: Mapped[str] = mapped_column(String(30), default="new", index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(30), default="medium", index=True, nullable=False)
    project_name: Mapped[str | None] = mapped_column(String(255)); property_code: Mapped[str | None] = mapped_column(String(100)); property_type: Mapped[str | None] = mapped_column(String(100)); area: Mapped[str | None] = mapped_column(String(255))
    expected_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2)); deposit_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2)); contract_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2)); commission_expected: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    expected_close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True); deposit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); contract_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lost_reason: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id")); assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True); deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    customer = relationship("Customer", back_populates="deals", lazy="joined")
    booking = relationship("Booking", foreign_keys=[booking_id], back_populates="deals")
    property_unit = relationship("PropertyUnit", back_populates="deals")
    project = relationship("Project", back_populates="deals")
    contracts = relationship("Contract", back_populates="deal", lazy="select")
    contract_payments = relationship("ContractPayment", back_populates="deal", lazy="select")
    source_lead = relationship("Lead", back_populates="deals", lazy="joined")
    owner = relationship("User", foreign_keys=[owner_id], lazy="joined"); creator = relationship("User", foreign_keys=[created_by_id], lazy="joined"); assigner = relationship("User", foreign_keys=[assigned_by_id], lazy="joined")
    activities = relationship("DealActivity", back_populates="deal", order_by="DealActivity.created_at.desc()", lazy="select", cascade="all, delete-orphan")
