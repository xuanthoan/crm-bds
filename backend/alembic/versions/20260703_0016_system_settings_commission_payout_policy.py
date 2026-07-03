"""system settings commission payout policy

Revision ID: 20260703_0016
Revises: 20260627_0015
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.dialects import postgresql

revision = "20260703_0016"
down_revision = "20260627_0015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'system_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('key', name='uq_system_settings_key'),
    )
    op.create_index('ix_system_settings_key', 'system_settings', ['key'])
    settings_table = sa.table(
        'system_settings',
        sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('key', sa.String),
        sa.column('value', sa.Text),
        sa.column('description', sa.Text),
        sa.column('created_at', sa.DateTime(timezone=True)),
        sa.column('updated_at', sa.DateTime(timezone=True)),
    )
    now = datetime.now(timezone.utc)
    op.bulk_insert(settings_table, [{
        'id': uuid4(),
        'key': 'sales_commission_payout_policy',
        'value': 'received_amount_capacity',
        'description': 'Cấu hình toàn hệ thống cho chính sách chi hoa hồng sale.',
        'created_at': now,
        'updated_at': now,
    }])


def downgrade():
    op.drop_index('ix_system_settings_key', table_name='system_settings')
    op.drop_table('system_settings')
