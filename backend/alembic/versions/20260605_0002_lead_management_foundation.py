"""Sprint 4 lead management foundation.

Revision ID: 20260605_0002
Revises: 20260603_0001
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260605_0002"
down_revision: str | None = "20260603_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone_primary", sa.String(length=50), nullable=False),
        sa.Column("phone_secondary", sa.String(length=50), nullable=True),
        sa.Column("zalo", sa.String(length=255), nullable=True),
        sa.Column("facebook", sa.String(length=500), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("project_interest", sa.String(length=255), nullable=True),
        sa.Column("location_interest", sa.String(length=255), nullable=True),
        sa.Column("budget_min", sa.Numeric(18, 2), nullable=True),
        sa.Column("budget_max", sa.Numeric(18, 2), nullable=True),
        sa.Column("bedroom_need", sa.Integer(), nullable=True),
        sa.Column("area_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("area_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="new"),
        sa.Column("priority", sa.String(length=30), nullable=False, server_default="medium"),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_contact_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("converted_customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lost_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["deleted_by"], ["users.id"]),
        sa.UniqueConstraint("code"),
    )
    for column in ("phone_primary", "phone_secondary", "status", "source", "owner_id", "created_by_id", "next_follow_up_at", "created_at"):
        op.create_index(f"ix_leads_{column}", "leads", [column])

    op.create_table(
        "lead_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activity_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("old_value", sa.String(length=255), nullable=True),
        sa.Column("new_value", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    for column in ("lead_id", "user_id", "activity_type", "created_at"):
        op.create_index(f"ix_lead_activities_{column}", "lead_activities", [column])


def downgrade() -> None:
    for column in ("created_at", "activity_type", "user_id", "lead_id"):
        op.drop_index(f"ix_lead_activities_{column}", table_name="lead_activities")
    op.drop_table("lead_activities")
    for column in ("created_at", "next_follow_up_at", "created_by_id", "owner_id", "source", "status", "phone_secondary", "phone_primary"):
        op.drop_index(f"ix_leads_{column}", table_name="leads")
    op.drop_table("leads")
