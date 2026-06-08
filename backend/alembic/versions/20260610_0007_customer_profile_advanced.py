"""Sprint 9 advanced customer profile and scoring.

Revision ID: 20260610_0007
Revises: 20260609_0006
Create Date: 2026-06-10
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260610_0007"
down_revision: str | None = "20260609_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    columns = [
        sa.Column("gender", sa.String(20)), sa.Column("date_of_birth", sa.Date()),
        sa.Column("province", sa.String(100)), sa.Column("district", sa.String(100)),
        sa.Column("occupation", sa.String(255)), sa.Column("company", sa.String(255)), sa.Column("job_title", sa.String(255)),
        sa.Column("expected_budget", sa.Numeric(18, 2)), sa.Column("available_cash", sa.Numeric(18, 2)),
        sa.Column("loan_needed", sa.Numeric(18, 2)), sa.Column("loan_ratio", sa.Numeric(5, 2)),
        sa.Column("preferred_bank", sa.String(255)), sa.Column("monthly_income", sa.Numeric(18, 2)),
        sa.Column("financial_rating", sa.String(20)), sa.Column("buying_purpose", sa.String(40)),
        sa.Column("interested_property_type", sa.String(40)), sa.Column("preferred_direction", sa.String(100)),
        sa.Column("preferred_view", sa.String(255)), sa.Column("buying_timeline", sa.String(40)),
        sa.Column("related_people_note", sa.Text()),
        sa.Column("score_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score_label", sa.String(30)), sa.Column("score_updated_at", sa.DateTime(timezone=True)), sa.Column("score_note", sa.Text()),
    ]
    for column in columns:
        op.add_column("customers", column)
    for column in ("gender", "province", "district", "financial_rating", "buying_purpose", "interested_property_type", "buying_timeline", "score_total", "score_label"):
        op.create_index(f"ix_customers_{column}", "customers", [column])
    op.create_index("ix_customers_owner_score_label", "customers", ["owner_id", "score_label"])
    op.create_index("ix_customers_owner_buying_timeline", "customers", ["owner_id", "buying_timeline"])
    op.create_index("ix_customers_owner_financial_rating", "customers", ["owner_id", "financial_rating"])
    op.create_table(
        "customer_related_people",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False), sa.Column("relationship", sa.String(30), nullable=False),
        sa.Column("phone", sa.String(50)), sa.Column("email", sa.String(255)), sa.Column("note", sa.Text()),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    for column in ("customer_id", "relationship", "phone", "deleted_at"):
        op.create_index(f"ix_customer_related_people_{column}", "customer_related_people", [column])
    op.create_index("ix_customer_related_people_customer_deleted", "customer_related_people", ["customer_id", "deleted_at"])


def downgrade() -> None:
    op.drop_table("customer_related_people")
    for name in ("ix_customers_owner_financial_rating", "ix_customers_owner_buying_timeline", "ix_customers_owner_score_label"):
        op.drop_index(name, table_name="customers")
    for column in ("score_label", "score_total", "buying_timeline", "interested_property_type", "buying_purpose", "financial_rating", "district", "province", "gender"):
        op.drop_index(f"ix_customers_{column}", table_name="customers")
    for column in ("score_note", "score_updated_at", "score_label", "score_total", "related_people_note", "buying_timeline", "preferred_view", "preferred_direction", "interested_property_type", "buying_purpose", "financial_rating", "monthly_income", "preferred_bank", "loan_ratio", "loan_needed", "available_cash", "expected_budget", "job_title", "company", "occupation", "district", "province", "date_of_birth", "gender"):
        op.drop_column("customers", column)
