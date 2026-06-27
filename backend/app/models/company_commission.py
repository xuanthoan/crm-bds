import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow(): return datetime.now(timezone.utc)

class CompanyCommissionReceivable(Base):
    __tablename__ = "company_commission_receivables"
    __table_args__ = (UniqueConstraint("contract_id", name="uq_company_commission_receivables_contract_id"), Index("ix_company_commission_receivables_code", "receivable_code"), Index("ix_company_commission_receivables_status", "status"), Index("ix_company_commission_receivables_created_at", "created_at"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receivable_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    company_role: Mapped[str] = mapped_column(String(50), default="broker", nullable=False)
    actual_seller_type: Mapped[str | None] = mapped_column(String(50))
    actual_seller_name: Mapped[str | None] = mapped_column(String(255))
    commission_payer_type: Mapped[str | None] = mapped_column(String(50))
    commission_payer_name: Mapped[str | None] = mapped_column(String(255))
    brokerage_contract_code: Mapped[str | None] = mapped_column(String(100))
    brokerage_policy_note: Mapped[str | None] = mapped_column(Text)
    contract_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    commission_rate_percent: Mapped[Decimal | None] = mapped_column(Numeric(7, 4))
    expected_commission_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    confirmed_receivable_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    received_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    expected_receive_date: Mapped[datetime | None] = mapped_column(Date)
    received_date: Mapped[datetime | None] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text)
    hold_reason: Mapped[str | None] = mapped_column(Text)
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    marked_received_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    cancelled_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    marked_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contract = relationship("Contract")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    marked_received_by = relationship("User", foreign_keys=[marked_received_by_id])
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_id])
    events = relationship("CompanyCommissionEvent", back_populates="receivable", order_by="CompanyCommissionEvent.created_at.desc()", cascade="all, delete-orphan")

class CompanyCommissionEvent(Base):
    __tablename__ = "company_commission_events"
    __table_args__ = (Index("ix_company_commission_events_receivable_id", "receivable_id"), Index("ix_company_commission_events_created_at", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receivable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("company_commission_receivables.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str | None] = mapped_column(String(30))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    note: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    receivable = relationship("CompanyCommissionReceivable", back_populates="events")
    created_by = relationship("User")
