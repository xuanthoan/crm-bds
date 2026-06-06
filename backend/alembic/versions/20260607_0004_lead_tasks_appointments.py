"""Sprint 6 lead tasks and appointments.

Revision ID: 20260607_0004
Revises: 20260606_0003
Create Date: 2026-06-07
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260607_0004"
down_revision: str | None = "20260606_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lead_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("task_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("completed_by_id", postgresql.UUID(as_uuid=True)),
        sa.Column("reminder_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("reminder_at", sa.DateTime(timezone=True)), sa.Column("result_note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["completed_by_id"], ["users.id"]),
        sa.CheckConstraint("reminder_at IS NULL OR reminder_at <= due_at", name="ck_lead_tasks_reminder_before_due"),
    )
    for column in ("lead_id", "assigned_to_id", "created_by_id", "status", "priority", "due_at", "reminder_at", "deleted_at"):
        op.create_index(f"ix_lead_tasks_{column}", "lead_tasks", [column])
    op.create_index("ix_lead_tasks_assigned_due", "lead_tasks", ["assigned_to_id", "due_at"])
    op.create_index("ix_lead_tasks_assigned_status", "lead_tasks", ["assigned_to_id", "status"])

    op.create_table(
        "lead_appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("appointment_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="scheduled"),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False), sa.Column("end_at", sa.DateTime(timezone=True)),
        sa.Column("location", sa.String(500)), sa.Column("meeting_link", sa.String(1000)),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("completed_by_id", postgresql.UUID(as_uuid=True)), sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("result_note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["completed_by_id"], ["users.id"]),
        sa.CheckConstraint("end_at IS NULL OR end_at > start_at", name="ck_lead_appointments_end_after_start"),
    )
    for column in ("lead_id", "assigned_to_id", "created_by_id", "status", "start_at", "deleted_at"):
        op.create_index(f"ix_lead_appointments_{column}", "lead_appointments", [column])
    op.create_index("ix_lead_appointments_assigned_start", "lead_appointments", ["assigned_to_id", "start_at"])
    op.create_index("ix_lead_appointments_assigned_status", "lead_appointments", ["assigned_to_id", "status"])


def downgrade() -> None:
    op.drop_table("lead_appointments")
    op.drop_table("lead_tasks")
