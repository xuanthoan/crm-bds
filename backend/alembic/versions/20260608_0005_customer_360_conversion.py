"""Sprint 7 Customer 360 and lead conversion.

Revision ID: 20260608_0005
Revises: 20260607_0004
Create Date: 2026-06-08
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260608_0005"
down_revision: str | None = "20260607_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("customer_code", sa.String(30), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("customer_type", sa.String(30), nullable=False, server_default="individual"),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("primary_phone", sa.String(50), nullable=False),
        sa.Column("secondary_phone", sa.String(50)), sa.Column("email", sa.String(255)),
        sa.Column("zalo", sa.String(255)), sa.Column("facebook", sa.String(500)), sa.Column("address", sa.Text()),
        sa.Column("source", sa.String(80)), sa.Column("source_lead_id", postgresql.UUID(as_uuid=True)), sa.Column("source_note", sa.Text()),
        sa.Column("interested_project", sa.String(255)), sa.Column("interested_area", sa.String(255)),
        sa.Column("budget_min", sa.Numeric(18, 2)), sa.Column("budget_max", sa.Numeric(18, 2)),
        sa.Column("bedroom_count", sa.Integer()), sa.Column("area_min", sa.Numeric(12, 2)), sa.Column("area_max", sa.Numeric(12, 2)),
        sa.Column("purpose", sa.String(30)), sa.Column("owner_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("updated_by_id", postgresql.UUID(as_uuid=True)),
        sa.Column("first_contact_at", sa.DateTime(timezone=True)), sa.Column("last_contact_at", sa.DateTime(timezone=True)),
        sa.Column("next_follow_up_at", sa.DateTime(timezone=True)), sa.Column("converted_at", sa.DateTime(timezone=True)),
        sa.Column("note", sa.Text()), sa.Column("deleted_at", sa.DateTime(timezone=True)), sa.Column("deleted_by_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["source_lead_id"], ["leads.id"]), sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]), sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"]),
    )
    for column in ("customer_code", "full_name", "primary_phone", "secondary_phone", "email", "status", "customer_type", "owner_id", "source_lead_id", "next_follow_up_at", "last_contact_at", "deleted_at"):
        op.create_index(f"ix_customers_{column}", "customers", [column])
    op.create_index("ix_customers_owner_status", "customers", ["owner_id", "status"])
    op.create_index("ix_customers_owner_next_follow_up", "customers", ["owner_id", "next_follow_up_at"])

    op.create_table(
        "customer_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("activity_type", sa.String(40), nullable=False), sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text()), sa.Column("old_value", sa.Text()), sa.Column("new_value", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    for column in ("customer_id", "user_id", "activity_type", "created_at"):
        op.create_index(f"ix_customer_activities_{column}", "customer_activities", [column])

    op.add_column("leads", sa.Column("converted_at", sa.DateTime(timezone=True)))
    op.add_column("leads", sa.Column("converted_by_id", postgresql.UUID(as_uuid=True)))
    op.create_foreign_key("fk_leads_converted_customer_id", "leads", "customers", ["converted_customer_id"], ["id"])
    op.create_foreign_key("fk_leads_converted_by_id", "leads", "users", ["converted_by_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_leads_converted_by_id", "leads", type_="foreignkey")
    op.drop_constraint("fk_leads_converted_customer_id", "leads", type_="foreignkey")
    op.drop_column("leads", "converted_by_id")
    op.drop_column("leads", "converted_at")
    op.drop_table("customer_activities")
    op.drop_table("customers")
