"""sales commissions workflow

Revision ID: 20260627_0014
Revises: 20260626_0013
Create Date: 2026-06-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260627_0014"
down_revision = "20260626_0013"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('sales_commissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('commission_code', sa.String(30), nullable=False, unique=True),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contracts.id'), nullable=False),
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('commission_rate_percent', sa.Numeric(7,4), nullable=False),
        sa.Column('contract_value', sa.Numeric(18,2), nullable=False),
        sa.Column('deposit_value', sa.Numeric(18,2), nullable=False, server_default='0'),
        sa.Column('confirmed_receipts_amount', sa.Numeric(18,2), nullable=False, server_default='0'),
        sa.Column('total_collected_with_deposit', sa.Numeric(18,2), nullable=False, server_default='0'),
        sa.Column('remaining_amount', sa.Numeric(18,2), nullable=False, server_default='0'),
        sa.Column('estimated_commission', sa.Numeric(18,2), nullable=False),
        sa.Column('collected_commission', sa.Numeric(18,2), nullable=False),
        sa.Column('eligible_commission', sa.Numeric(18,2), nullable=False),
        sa.Column('approved_commission', sa.Numeric(18,2), nullable=False, server_default='0'),
        sa.Column('paid_amount', sa.Numeric(18,2), nullable=False, server_default='0'),
        sa.Column('status', sa.String(30), nullable=False, server_default='eligible'),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('paid_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('paid_at', sa.DateTime(timezone=True)),
        sa.Column('cancel_reason', sa.Text()), sa.Column('hold_reason', sa.Text()), sa.Column('note', sa.Text()),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('contract_id', name='uq_sales_commissions_contract_id'))
    for c in ['code','status','sale_id','created_at','approved_at','paid_at']:
        op.create_index(f'ix_sales_commissions_{c}', 'sales_commissions', ['commission_code' if c=='code' else c])
    op.create_table('sales_commission_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('commission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sales_commissions.id'), nullable=False),
        sa.Column('event_type', sa.String(30), nullable=False), sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()), sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_sales_commission_events_commission_id','sales_commission_events',['commission_id'])
    op.create_index('ix_sales_commission_events_created_at','sales_commission_events',['created_at'])

def downgrade():
    op.drop_table('sales_commission_events'); op.drop_table('sales_commissions')
