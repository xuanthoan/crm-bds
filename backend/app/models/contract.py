import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow(): return datetime.now(timezone.utc)

class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = (Index("ix_contracts_deal_id", "deal_id"), Index("ix_contracts_booking_id", "booking_id"), Index("ix_contracts_customer_id", "customer_id"), Index("ix_contracts_property_unit_id", "property_unit_id"), Index("ix_contracts_project_id", "project_id"), Index("ix_contracts_status", "status"), Index("ix_contracts_signed_date", "signed_date"), Index("ix_contracts_deleted_at", "deleted_at"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    deal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id"))
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    property_unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("property_units.id"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
    contract_type: Mapped[str] = mapped_column(String(30), default="deposit_contract", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    contract_number: Mapped[str | None] = mapped_column(String(100)); signed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); effective_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); handover_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contract_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False); deposit_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2)); remaining_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    buyer_name: Mapped[str | None] = mapped_column(String(255)); buyer_phone: Mapped[str | None] = mapped_column(String(50)); buyer_email: Mapped[str | None] = mapped_column(String(255)); buyer_id_number: Mapped[str | None] = mapped_column(String(100)); buyer_address: Mapped[str | None] = mapped_column(Text)
    seller_name: Mapped[str | None] = mapped_column(String(255)); seller_phone: Mapped[str | None] = mapped_column(String(50)); seller_email: Mapped[str | None] = mapped_column(String(255)); seller_representative: Mapped[str | None] = mapped_column(String(255)); note: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False); updated_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id")); deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False); deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deal=relationship("Deal",back_populates="contracts"); booking=relationship("Booking",back_populates="contracts"); customer=relationship("Customer",back_populates="contracts"); property_unit=relationship("PropertyUnit",back_populates="contracts"); project=relationship("Project",back_populates="contracts")
    creator=relationship("User",foreign_keys=[created_by_id]); updater=relationship("User",foreign_keys=[updated_by_id]); deleter=relationship("User",foreign_keys=[deleted_by_id])
    payments=relationship("ContractPayment",back_populates="contract",order_by="ContractPayment.created_at.desc()",cascade="all, delete-orphan"); activities=relationship("ContractActivity",back_populates="contract",order_by="ContractActivity.created_at.desc()",cascade="all, delete-orphan")
