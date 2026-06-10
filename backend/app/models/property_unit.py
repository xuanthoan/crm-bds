import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow() -> datetime: return datetime.now(timezone.utc)

class PropertyUnit(Base):
    __tablename__ = "property_units"
    __table_args__ = (
        Index("ix_property_units_project_status", "project_id", "inventory_status"),
        Index("ix_property_units_project_type", "project_id", "property_type"),
        Index("ix_property_units_type_status", "property_type", "inventory_status"),
        Index("ix_property_units_listed_price_status", "listed_price", "inventory_status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    property_type: Mapped[str] = mapped_column(String(30), default="apartment", index=True, nullable=False)
    inventory_status: Mapped[str] = mapped_column(String(30), default="available", index=True, nullable=False)
    block: Mapped[str | None] = mapped_column(String(100)); tower: Mapped[str | None] = mapped_column(String(100)); floor: Mapped[str | None] = mapped_column(String(100)); unit_number: Mapped[str | None] = mapped_column(String(100))
    bedroom_count: Mapped[int | None] = mapped_column(Integer, index=True); bathroom_count: Mapped[int | None] = mapped_column(Integer)
    area_gross: Mapped[Decimal | None] = mapped_column(Numeric(18, 2)); area_net: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), index=True); balcony_area: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    door_direction: Mapped[str | None] = mapped_column(String(50)); balcony_direction: Mapped[str | None] = mapped_column(String(50)); view_description: Mapped[str | None] = mapped_column(String(255))
    listed_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), index=True); owner_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), index=True); minimum_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), index=True); last_transaction_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    commission_type: Mapped[str | None] = mapped_column(String(30)); commission_fixed: Mapped[Decimal | None] = mapped_column(Numeric(18, 2)); commission_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    owner_name: Mapped[str | None] = mapped_column(String(255)); owner_phone: Mapped[str | None] = mapped_column(String(50)); owner_email: Mapped[str | None] = mapped_column(String(255)); owner_note: Mapped[str | None] = mapped_column(Text)
    legal_status: Mapped[str | None] = mapped_column(String(40), index=True); legal_note: Mapped[str | None] = mapped_column(Text)
    media_images: Mapped[str | None] = mapped_column(Text); media_videos: Mapped[str | None] = mapped_column(Text); media_documents: Mapped[str | None] = mapped_column(Text); media_drive_links: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(100)); note: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id")); deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False); deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    project = relationship("Project", back_populates="property_units", lazy="joined")
    creator = relationship("User", foreign_keys=[created_by_id], lazy="joined"); updater = relationship("User", foreign_keys=[updated_by_id], lazy="joined"); deleter = relationship("User", foreign_keys=[deleted_by_id], lazy="joined")
    price_history = relationship("PropertyPriceHistory", back_populates="property_unit", order_by="PropertyPriceHistory.created_at.desc()", cascade="all, delete-orphan")
    status_history = relationship("PropertyStatusHistory", back_populates="property_unit", order_by="PropertyStatusHistory.created_at.desc()", cascade="all, delete-orphan")
