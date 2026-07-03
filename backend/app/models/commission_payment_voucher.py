import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow(): return datetime.now(timezone.utc)

class SalesCommissionPaymentVoucher(Base):
    __tablename__ = "sales_commission_payment_vouchers"
    __table_args__ = (
        UniqueConstraint("code", name="uq_sales_commission_payment_vouchers_code"),
        CheckConstraint("amount > 0", name="ck_sales_commission_payment_vouchers_amount_positive"),
        Index("ix_scpv_sales_commission_id", "sales_commission_id"), Index("ix_scpv_contract_id", "contract_id"),
        Index("ix_scpv_sale_id", "sale_id"), Index("ix_scpv_status", "status"), Index("ix_scpv_payment_date", "payment_date"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    sales_commission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_commissions.id"), nullable=False)
    contract_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id"))
    sale_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    paid_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    cancelled_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    attachment_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    commission = relationship("SalesCommission", back_populates="payment_vouchers")
    contract = relationship("Contract")
    sale = relationship("User", foreign_keys=[sale_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    paid_by = relationship("User", foreign_keys=[paid_by_id])
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_id])
