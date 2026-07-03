import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow(): return datetime.now(timezone.utc)

class SalesCommission(Base):
    __tablename__ = "sales_commissions"
    __table_args__ = (UniqueConstraint("contract_id", name="uq_sales_commissions_contract_id"), Index("ix_sales_commissions_code", "commission_code"), Index("ix_sales_commissions_status", "status"), Index("ix_sales_commissions_sale_id", "sale_id"), Index("ix_sales_commissions_created_at", "created_at"), Index("ix_sales_commissions_approved_at", "approved_at"), Index("ix_sales_commissions_paid_at", "paid_at"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commission_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    sale_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    commission_rate_percent: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    contract_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    deposit_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    confirmed_receipts_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total_collected_with_deposit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    estimated_commission: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    collected_commission: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    eligible_commission: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    approved_commission: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    payout_policy_code: Mapped[str | None] = mapped_column(String(50))
    payout_policy_source: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="eligible", nullable=False)
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    hold_reason: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    contract = relationship("Contract")
    sale = relationship("User", foreign_keys=[sale_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    paid_by = relationship("User", foreign_keys=[paid_by_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    events = relationship("SalesCommissionEvent", back_populates="commission", order_by="SalesCommissionEvent.created_at.desc()", cascade="all, delete-orphan")

class SalesCommissionEvent(Base):
    __tablename__ = "sales_commission_events"
    __table_args__ = (Index("ix_sales_commission_events_commission_id", "commission_id"), Index("ix_sales_commission_events_created_at", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_commissions.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    commission = relationship("SalesCommission", back_populates="events")
    actor = relationship("User")
