"""Sprint 5 organization structure and real lead scope.

Revision ID: 20260606_0003
Revises: 20260605_0002
Create Date: 2026-06-06
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260606_0003"
down_revision: str | None = "20260605_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"]),
        sa.UniqueConstraint("code"),
    )
    for column in ("code", "name", "manager_id", "status"):
        op.create_index(f"ix_departments_{column}", "departments", [column], unique=column == "code")

    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("leader_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["leader_id"], ["users.id"]),
        sa.UniqueConstraint("code"),
    )
    for column in ("department_id", "code", "name", "leader_id", "status"):
        op.create_index(f"ix_teams_{column}", "teams", [column], unique=column == "code")

    op.create_table(
        "user_organization_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("position_title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.UniqueConstraint("user_id", "department_id", "team_id", name="uq_user_organization_membership"),
        sa.CheckConstraint("department_id IS NOT NULL OR team_id IS NOT NULL", name="ck_membership_has_organization"),
    )
    for column in ("user_id", "department_id", "team_id", "is_primary"):
        op.create_index(f"ix_memberships_{column}", "user_organization_memberships", [column])


def downgrade() -> None:
    for column in ("is_primary", "team_id", "department_id", "user_id"):
        op.drop_index(f"ix_memberships_{column}", table_name="user_organization_memberships")
    op.drop_table("user_organization_memberships")
    for column in ("status", "leader_id", "name", "code", "department_id"):
        op.drop_index(f"ix_teams_{column}", table_name="teams")
    op.drop_table("teams")
    for column in ("status", "manager_id", "name", "code"):
        op.drop_index(f"ix_departments_{column}", table_name="departments")
    op.drop_table("departments")
