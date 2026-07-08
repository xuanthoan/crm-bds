"""Sprint 30 task comments timeline links

Revision ID: 20260707_0021
Revises: 20260706_0020
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20260707_0021"
down_revision = "20260706_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing = set(inspect(op.get_bind()).get_table_names())
    if "task_comments" not in existing:
        op.create_table(
            "task_comments",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
            sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("idx_task_comments_task_id_created_at", "task_comments", ["task_id", "created_at"])
        op.create_index("idx_task_comments_author_id", "task_comments", ["author_id"])
    if "task_related_links" not in existing:
        op.create_table(
            "task_related_links",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("url", sa.Text(), nullable=False),
            sa.Column("note", sa.Text()),
            sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("idx_task_related_links_task_id_created_at", "task_related_links", ["task_id", "created_at"])
        op.create_index("idx_task_related_links_created_by_id", "task_related_links", ["created_by_id"])


def downgrade() -> None:
    existing = set(inspect(op.get_bind()).get_table_names())
    if "task_related_links" in existing:
        op.drop_table("task_related_links")
    if "task_comments" in existing:
        op.drop_table("task_comments")
