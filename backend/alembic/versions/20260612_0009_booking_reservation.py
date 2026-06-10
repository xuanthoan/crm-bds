"""booking reservation and deposit foundation

Revision ID: 20260612_0009
Revises: 20260611_0008
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260612_0009"
down_revision = "20260611_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("booking_code", sa.String(30), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("property_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("property_units.id"), nullable=False),
        sa.Column("source_lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id")),
        sa.Column("source_deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id")),
        sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("booking_amount", sa.Numeric(18, 2)),
        sa.Column("deposit_amount", sa.Numeric(18, 2)),
        sa.Column("refund_amount", sa.Numeric(18, 2)),
        sa.Column("booking_date", sa.DateTime(timezone=True)),
        sa.Column("reservation_expires_at", sa.DateTime(timezone=True)),
        sa.Column("deposit_date", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("refunded_at", sa.DateTime(timezone=True)),
        sa.Column("cancel_reason", sa.Text()),
        sa.Column("refund_reason", sa.Text()),
        sa.Column("note", sa.Text()),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("deleted_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("booking_code", name="uq_bookings_booking_code"),
    )
    for column in ("customer_id", "property_unit_id", "assigned_user_id", "source_lead_id", "source_deal_id", "status", "booking_date", "reservation_expires_at", "deposit_date", "deleted_at"):
        op.create_index(f"ix_bookings_{column}", "bookings", [column])
    op.create_index("ix_bookings_property_status", "bookings", ["property_unit_id", "status"])
    op.create_index("ix_bookings_assigned_status", "bookings", ["assigned_user_id", "status"])
    op.create_index("ix_bookings_customer_status", "bookings", ["customer_id", "status"])
    op.create_index(
        "uq_bookings_active_property",
        "bookings",
        ["property_unit_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND status IN ('draft', 'reserved', 'deposited')"),
    )
    op.create_table(
        "booking_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activity_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("old_value", sa.Text()),
        sa.Column("new_value", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("booking_id", "actor_id", "activity_type", "created_at"):
        op.create_index(f"ix_booking_activities_{column}", "booking_activities", [column])


def downgrade() -> None:
    op.drop_table("booking_activities")
    op.drop_table("bookings")
