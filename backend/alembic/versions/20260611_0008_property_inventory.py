"""Sprint 10 property inventory foundation.

Revision ID: 20260611_0008
Revises: 20260610_0007
Create Date: 2026-06-11
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
revision: str = "20260611_0008"
down_revision: str | None = "20260610_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table("projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_code", sa.String(30), unique=True, nullable=False), sa.Column("name", sa.String(255), nullable=False),
        sa.Column("developer", sa.String(255)), sa.Column("description", sa.Text()), sa.Column("address", sa.Text()),
        sa.Column("province", sa.String(100)), sa.Column("district", sa.String(100)), sa.Column("ward", sa.String(100)),
        sa.Column("project_type", sa.String(40)), sa.Column("status", sa.String(30), nullable=False, server_default="planning"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")), sa.Column("deleted_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("deleted_at", sa.DateTime(timezone=True)))
    for column in ("project_code", "name", "developer", "province", "district", "project_type", "status", "deleted_at", "created_at"):
        op.create_index(f"ix_projects_{column}", "projects", [column], unique=column == "project_code")
    op.create_table("property_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_code", sa.String(30), unique=True, nullable=False), sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id")),
        sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("property_type", sa.String(30), nullable=False, server_default="apartment"), sa.Column("inventory_status", sa.String(30), nullable=False, server_default="available"),
        sa.Column("block", sa.String(100)), sa.Column("tower", sa.String(100)), sa.Column("floor", sa.String(100)), sa.Column("unit_number", sa.String(100)),
        sa.Column("bedroom_count", sa.Integer()), sa.Column("bathroom_count", sa.Integer()),
        sa.Column("area_gross", sa.Numeric(18,2)), sa.Column("area_net", sa.Numeric(18,2)), sa.Column("balcony_area", sa.Numeric(18,2)),
        sa.Column("door_direction", sa.String(50)), sa.Column("balcony_direction", sa.String(50)), sa.Column("view_description", sa.String(255)),
        sa.Column("listed_price", sa.Numeric(18,2)), sa.Column("owner_price", sa.Numeric(18,2)), sa.Column("minimum_price", sa.Numeric(18,2)), sa.Column("last_transaction_price", sa.Numeric(18,2)),
        sa.Column("commission_type", sa.String(30)), sa.Column("commission_fixed", sa.Numeric(18,2)), sa.Column("commission_rate", sa.Numeric(8,2)),
        sa.Column("owner_name", sa.String(255)), sa.Column("owner_phone", sa.String(50)), sa.Column("owner_email", sa.String(255)), sa.Column("owner_note", sa.Text()),
        sa.Column("legal_status", sa.String(40)), sa.Column("legal_note", sa.Text()),
        sa.Column("media_images", sa.Text()), sa.Column("media_videos", sa.Text()), sa.Column("media_documents", sa.Text()), sa.Column("media_drive_links", sa.Text()),
        sa.Column("source", sa.String(100)), sa.Column("note", sa.Text()),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")), sa.Column("deleted_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("deleted_at", sa.DateTime(timezone=True)))
    for column in ("property_code", "project_id", "property_type", "inventory_status", "bedroom_count", "area_net", "listed_price", "owner_price", "minimum_price", "legal_status", "created_at", "deleted_at"):
        op.create_index(f"ix_property_units_{column}", "property_units", [column], unique=column == "property_code")
    for name, columns in (("project_status", ["project_id","inventory_status"]),("project_type",["project_id","property_type"]),("type_status",["property_type","inventory_status"]),("listed_price_status",["listed_price","inventory_status"])):
        op.create_index(f"ix_property_units_{name}", "property_units", columns)
    op.create_table("property_price_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")), sa.Column("property_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("property_units.id", ondelete="CASCADE"), nullable=False), sa.Column("changed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("field_name", sa.String(50), nullable=False), sa.Column("old_value", sa.Numeric(18,2)), sa.Column("new_value", sa.Numeric(18,2)), sa.Column("note", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    for column in ("property_unit_id","field_name","changed_by_id","created_at"): op.create_index(f"ix_property_price_history_{column}", "property_price_history", [column])
    op.create_index("ix_property_price_history_property_created", "property_price_history", ["property_unit_id","created_at"])
    op.create_table("property_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")), sa.Column("property_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("property_units.id", ondelete="CASCADE"), nullable=False), sa.Column("changed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("old_status", sa.String(30)), sa.Column("new_status", sa.String(30), nullable=False), sa.Column("note", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    for column in ("property_unit_id","new_status","changed_by_id","created_at"): op.create_index(f"ix_property_status_history_{column}", "property_status_history", [column])
    op.create_index("ix_property_status_history_property_created", "property_status_history", ["property_unit_id","created_at"])

def downgrade() -> None:
    op.drop_table("property_status_history"); op.drop_table("property_price_history"); op.drop_table("property_units"); op.drop_table("projects")
