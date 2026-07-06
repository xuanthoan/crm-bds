"""Sprint 29 task collaboration

Revision ID: 20260706_0020
Revises: 20260704_0019
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20260706_0020"
down_revision = "20260704_0019"
branch_labels = None
depends_on = None


def _create_join_table(name, uq_name):
    op.create_table(
        name,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("task_id", "user_id", name=uq_name),
    )
    op.create_index(f"ix_{name}_task_id", name, ["task_id"])
    op.create_index(f"ix_{name}_user_id", name, ["user_id"])


def upgrade() -> None:
    existing = set(inspect(op.get_bind()).get_table_names())
    if "task_assignees" not in existing:
        _create_join_table("task_assignees", "uq_task_assignees_task_user")
    if "task_watchers" not in existing:
        _create_join_table("task_watchers", "uq_task_watchers_task_user")
    op.execute("""
        INSERT INTO task_assignees (id, task_id, user_id, created_by_id, created_at)
        SELECT gen_random_uuid(), id, assigned_user_id, created_by_id, COALESCE(created_at, now())
        FROM tasks
        WHERE assigned_user_id IS NOT NULL
        ON CONFLICT (task_id, user_id) DO NOTHING
    """)
    op.execute("""
        INSERT INTO task_watchers (id, task_id, user_id, created_by_id, created_at)
        SELECT gen_random_uuid(), id, created_by_id, created_by_id, COALESCE(created_at, now())
        FROM tasks
        WHERE created_by_id IS NOT NULL AND (assigned_user_id IS NULL OR created_by_id <> assigned_user_id)
        ON CONFLICT (task_id, user_id) DO NOTHING
    """)


def downgrade() -> None:
    existing = set(inspect(op.get_bind()).get_table_names())
    if "task_watchers" in existing:
        op.drop_table("task_watchers")
    if "task_assignees" in existing:
        op.drop_table("task_assignees")
