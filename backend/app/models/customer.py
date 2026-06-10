import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date as SQLDate, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_owner_status", "owner_id", "status"),
        Index("ix_customers_owner_next_follow_up", "owner_id", "next_follow_up_at"),
        Index("ix_customers_owner_score_label", "owner_id", "score_label"),
        Index("ix_customers_owner_buying_timeline", "owner_id", "buying_timeline"),
        Index("ix_customers_owner_financial_rating", "owner_id", "financial_rating"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    customer_type: Mapped[str] = mapped_column(String(30), index=True, default="individual", nullable=False)
    status: Mapped[str] = mapped_column(String(30), index=True, default="active", nullable=False)
    primary_phone: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    secondary_phone: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    zalo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(500), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(SQLDate, nullable=True)
    province: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expected_budget: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    available_cash: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    loan_needed: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    loan_ratio: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    preferred_bank: Mapped[str | None] = mapped_column(String(255), nullable=True)
    monthly_income: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    financial_rating: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    buying_purpose: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    interested_property_type: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    preferred_direction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_view: Mapped[str | None] = mapped_column(String(255), nullable=True)
    buying_timeline: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    related_people_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_total: Mapped[int] = mapped_column(Integer, index=True, default=0, nullable=False)
    score_label: Mapped[str | None] = mapped_column(String(30), index=True, nullable=True)
    score_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"), index=True, nullable=True)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    interested_project: Mapped[str | None] = mapped_column(String(255), nullable=True)
    interested_area: Mapped[str | None] = mapped_column(String(255), nullable=True)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    bedroom_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    area_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(30), nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    first_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id], lazy="joined")
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")
    updated_by = relationship("User", foreign_keys=[updated_by_id], lazy="joined")
    source_lead = relationship("Lead", foreign_keys=[source_lead_id], back_populates="source_customer", lazy="joined")
    deals = relationship("Deal", back_populates="customer", lazy="select")
    bookings = relationship("Booking", back_populates="customer", lazy="select")
    activities = relationship("CustomerActivity", back_populates="customer", cascade="all, delete-orphan", order_by="CustomerActivity.created_at.desc()")
    related_people = relationship("CustomerRelatedPerson", back_populates="customer", cascade="all, delete-orphan", order_by="CustomerRelatedPerson.created_at.desc()")
