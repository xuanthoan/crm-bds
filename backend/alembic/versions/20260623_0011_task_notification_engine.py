"""task and in-app notification engine

Revision ID: 20260623_0011
Revises: 20260613_0010
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260623_0011"
down_revision = "20260613_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_code", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("task_type", sa.String(40), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("related_customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id")),
        sa.Column("related_lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id")),
        sa.Column("related_booking_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bookings.id")),
        sa.Column("related_deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id")),
        sa.Column("related_contract_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contracts.id")),
        sa.Column("related_property_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("property_units.id")),
        sa.Column("auto_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_event", sa.String(80)),
        sa.Column("note", sa.Text()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("task_code", name="uq_tasks_task_code"),
    )
    op.create_index("ix_tasks_task_code", "tasks", ["task_code"])
    op.create_index("ix_tasks_assigned_user_id", "tasks", ["assigned_user_id"])
    op.create_index("ix_tasks_due_at", "tasks", ["due_at"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_source_booking", "tasks", ["source_event", "related_booking_id"])
    op.create_index("ix_tasks_source_contract", "tasks", ["source_event", "related_contract_id"])

    op.create_table(
        "task_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activity_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("old_value", sa.String(255)),
        sa.Column("new_value", sa.String(255)),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("task_id", "activity_type", "actor_id", "created_at"):
        op.create_index(f"ix_task_activities_{column}", "task_activities", [column])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recipient_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="unread"),
        sa.Column("related_task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id")),
        sa.Column("related_booking_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bookings.id")),
        sa.Column("related_deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id")),
        sa.Column("related_contract_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contracts.id")),
        sa.Column("related_customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id")),
        sa.Column("related_property_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("property_units.id")),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_notifications_recipient_user_id", "notifications", ["recipient_user_id"])
    op.create_index("ix_notifications_read_at", "notifications", ["read_at"])
    op.create_index("ix_notifications_status", "notifications", ["status"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("task_activities")
    op.drop_table("tasks")
