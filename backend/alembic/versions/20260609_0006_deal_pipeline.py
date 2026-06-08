"""Sprint 8 Deal Pipeline foundation.

Revision ID: 20260609_0006
Revises: 20260608_0005
Create Date: 2026-06-09
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260609_0006"
down_revision: str | None = "20260608_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("deal_code", sa.String(30), nullable=False, unique=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("source_lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id")),
        sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("deal_type", sa.String(30), nullable=False, server_default="apartment"),
        sa.Column("pipeline_stage", sa.String(30), nullable=False, server_default="new"),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(30), nullable=False, server_default="medium"),
        sa.Column("project_name", sa.String(255)), sa.Column("property_code", sa.String(100)),
        sa.Column("property_type", sa.String(100)), sa.Column("area", sa.String(255)),
        sa.Column("expected_value", sa.Numeric(18, 2)), sa.Column("deposit_amount", sa.Numeric(18, 2)),
        sa.Column("contract_value", sa.Numeric(18, 2)), sa.Column("commission_expected", sa.Numeric(18, 2)),
        sa.Column("expected_close_date", sa.DateTime(timezone=True)), sa.Column("deposit_date", sa.DateTime(timezone=True)),
        sa.Column("contract_date", sa.DateTime(timezone=True)), sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("lost_reason", sa.Text()),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("assigned_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
    )
    for column in ("customer_id", "owner_id", "pipeline_stage", "status", "priority", "expected_close_date", "created_at", "deleted_at"):
        op.create_index(f"ix_deals_{column}", "deals", [column])
    op.create_index("ix_deals_owner_status", "deals", ["owner_id", "status"])
    op.create_index("ix_deals_pipeline_stage_status", "deals", ["pipeline_stage", "status"])
    op.create_index("ix_deals_customer_deleted_at", "deals", ["customer_id", "deleted_at"])
    op.create_table(
        "deal_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activity_type", sa.String(40), nullable=False), sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text()), sa.Column("old_value", sa.Text()), sa.Column("new_value", sa.Text()),
        sa.Column("metadata_json", postgresql.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in ("deal_id", "user_id", "activity_type", "created_at"):
        op.create_index(f"ix_deal_activities_{column}", "deal_activities", [column])
    op.create_index("ix_deal_activities_deal_created_at", "deal_activities", ["deal_id", "created_at"])


def downgrade() -> None:
    op.drop_table("deal_activities")
    op.drop_table("deals")
