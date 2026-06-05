"""lead management foundation

Revision ID: 20260605_0002
Revises: 20260603_0001
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
        sa.Column("code", sa.String(20), nullable=False), sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone_primary", sa.String(50), nullable=False), sa.Column("phone_secondary", sa.String(50)),
        sa.Column("zalo", sa.String(255)), sa.Column("facebook", sa.String(500)), sa.Column("email", sa.String(255)),
        sa.Column("address", sa.Text()), sa.Column("source", sa.String(80)), sa.Column("project_interest", sa.String(255)),
        sa.Column("location_interest", sa.String(255)), sa.Column("budget_min", sa.Numeric(18, 2)), sa.Column("budget_max", sa.Numeric(18, 2)),
        sa.Column("bedroom_need", sa.Integer()), sa.Column("area_min", sa.Numeric(12, 2)), sa.Column("area_max", sa.Numeric(12, 2)),
        sa.Column("note", sa.Text()), sa.Column("status", sa.String(40), nullable=False, server_default="new"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("assigned_at", sa.DateTime(timezone=True)), sa.Column("last_contact_at", sa.DateTime(timezone=True)),
        sa.Column("next_follow_up_at", sa.DateTime(timezone=True)), sa.Column("converted_customer_id", postgresql.UUID(as_uuid=True)),
        sa.Column("lost_reason", sa.String(500)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)), sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
    )
    for name, columns, unique in [
        ("ix_leads_code", ["code"], True), ("ix_leads_phone_primary", ["phone_primary"], False),
        ("ix_leads_phone_secondary", ["phone_secondary"], False), ("ix_leads_status", ["status"], False),
        ("ix_leads_source", ["source"], False), ("ix_leads_owner_id", ["owner_id"], False),
        ("ix_leads_created_by_id", ["created_by_id"], False), ("ix_leads_next_follow_up_at", ["next_follow_up_at"], False),
        ("ix_leads_created_at", ["created_at"], False),
    ]: op.create_index(name, "leads", columns, unique=unique)
    op.create_table(
        "lead_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activity_type", sa.String(40), nullable=False), sa.Column("title", sa.String(255)),
        sa.Column("content", sa.Text(), nullable=False), sa.Column("old_value", sa.String(255)), sa.Column("new_value", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in ("lead_id", "user_id", "activity_type", "created_at"):
        op.create_index(f"ix_lead_activities_{column}", "lead_activities", [column])


def downgrade() -> None:
    op.drop_table("lead_activities")
    op.drop_table("leads")
