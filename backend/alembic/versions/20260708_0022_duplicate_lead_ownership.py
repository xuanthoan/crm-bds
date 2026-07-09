"""Sprint 31 duplicate lead ownership

Revision ID: 20260708_0022
Revises: 20260707_0021
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20260708_0022"
down_revision = "20260707_0021"
branch_labels = None
depends_on = None


def _add_column(table: str, column: sa.Column) -> None:
    columns = {c["name"] for c in inspect(op.get_bind()).get_columns(table)}
    if column.name not in columns:
        op.add_column(table, column)


def _create_index(name: str, table: str, columns: list[str]) -> None:
    indexes = {idx["name"] for idx in inspect(op.get_bind()).get_indexes(table)}
    if name not in indexes:
        op.create_index(name, table, columns)


def upgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    if "customers" in tables:
        _add_column("customers", sa.Column("phone_primary_normalized", sa.String(50), nullable=True))
        _add_column("customers", sa.Column("phone_secondary_normalized", sa.String(50), nullable=True))
        _add_column("customers", sa.Column("first_lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=True))
        _add_column("customers", sa.Column("first_touch_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
        _add_column("customers", sa.Column("first_touch_source", sa.String(80), nullable=True))
        _add_column("customers", sa.Column("first_uploaded_at", sa.DateTime(timezone=True), nullable=True))
        _add_column("customers", sa.Column("first_upload_note", sa.Text(), nullable=True))
        _add_column("customers", sa.Column("is_duplicate_profile", sa.Boolean(), nullable=False, server_default=sa.false()))
        _create_index("ix_customers_phone_primary_normalized", "customers", ["phone_primary_normalized"])
        _create_index("ix_customers_phone_secondary_normalized", "customers", ["phone_secondary_normalized"])
        _create_index("ix_customers_first_lead_id", "customers", ["first_lead_id"])
        _create_index("ix_customers_first_touch_user_id", "customers", ["first_touch_user_id"])
    if "leads" in tables:
        _add_column("leads", sa.Column("phone_primary_normalized", sa.String(50), nullable=True))
        _add_column("leads", sa.Column("phone_secondary_normalized", sa.String(50), nullable=True))
        _add_column("leads", sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=True))
        _add_column("leads", sa.Column("duplicate_of_customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=True))
        _add_column("leads", sa.Column("duplicate_detected", sa.Boolean(), nullable=False, server_default=sa.false()))
        _add_column("leads", sa.Column("duplicate_match_reason", sa.Text(), nullable=True))
        for name, cols in {
            "ix_leads_phone_primary_normalized": ["phone_primary_normalized"],
            "ix_leads_phone_secondary_normalized": ["phone_secondary_normalized"],
            "ix_leads_customer_id": ["customer_id"],
            "ix_leads_duplicate_of_customer_id": ["duplicate_of_customer_id"],
        }.items():
            _create_index(name, "leads", cols)


def downgrade() -> None:
    pass
