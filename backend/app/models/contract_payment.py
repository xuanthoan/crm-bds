import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow(): return datetime.now(timezone.utc)
class ContractPayment(Base):
    __tablename__="contract_payments"
    __table_args__=tuple(Index(f"ix_contract_payments_{c}",c) for c in ("contract_id","deal_id","customer_id","property_unit_id","status","due_date","paid_date","deleted_at"))
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); payment_code:Mapped[str]=mapped_column(String(30),unique=True,nullable=False)
    contract_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("contracts.id"),nullable=False); deal_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("deals.id"),nullable=False); customer_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("customers.id"),nullable=False); property_unit_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("property_units.id"),nullable=False)
    payment_type:Mapped[str]=mapped_column(String(30),default="payment",nullable=False); status:Mapped[str]=mapped_column(String(30),default="planned",nullable=False); amount:Mapped[Decimal]=mapped_column(Numeric(18,2),nullable=False); due_date:Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); paid_date:Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); payment_method:Mapped[str|None]=mapped_column(String(100)); reference_number:Mapped[str|None]=mapped_column(String(100)); note:Mapped[str|None]=mapped_column(Text)
    created_by_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),nullable=False); updated_by_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id")); deleted_by_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id")); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,nullable=False); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,onupdate=utcnow,nullable=False); deleted_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    contract=relationship("Contract",back_populates="payments"); deal=relationship("Deal",back_populates="contract_payments"); customer=relationship("Customer",back_populates="contract_payments"); property_unit=relationship("PropertyUnit",back_populates="contract_payments"); creator=relationship("User",foreign_keys=[created_by_id]); updater=relationship("User",foreign_keys=[updated_by_id]); deleter=relationship("User",foreign_keys=[deleted_by_id])
