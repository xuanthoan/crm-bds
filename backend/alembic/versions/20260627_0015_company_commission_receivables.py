"""company commission receivables

Revision ID: 20260627_0015
Revises: 20260627_0014
Create Date: 2026-06-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260627_0015"
down_revision = "20260627_0014"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('contracts', sa.Column('company_role', sa.String(50), nullable=False, server_default='broker'))
    op.add_column('contracts', sa.Column('actual_seller_type', sa.String(50)))
    op.add_column('contracts', sa.Column('actual_seller_name', sa.String(255)))
    op.add_column('contracts', sa.Column('commission_payer_type', sa.String(50)))
    op.add_column('contracts', sa.Column('commission_payer_name', sa.String(255)))
    op.add_column('contracts', sa.Column('brokerage_contract_code', sa.String(100)))
    op.add_column('contracts', sa.Column('brokerage_policy_note', sa.Text()))
    op.create_table('company_commission_receivables',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('receivable_code', sa.String(30), nullable=False, unique=True),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contracts.id'), nullable=False),
        sa.Column('company_role', sa.String(50), nullable=False, server_default='broker'),
        sa.Column('actual_seller_type', sa.String(50)), sa.Column('actual_seller_name', sa.String(255)),
        sa.Column('commission_payer_type', sa.String(50)), sa.Column('commission_payer_name', sa.String(255)),
        sa.Column('brokerage_contract_code', sa.String(100)), sa.Column('brokerage_policy_note', sa.Text()),
        sa.Column('contract_value', sa.Numeric(18,2), nullable=False), sa.Column('commission_rate_percent', sa.Numeric(7,4)),
        sa.Column('expected_commission_amount', sa.Numeric(18,2), nullable=False),
        sa.Column('confirmed_receivable_amount', sa.Numeric(18,2), nullable=False, server_default='0'),
        sa.Column('received_amount', sa.Numeric(18,2), nullable=False, server_default='0'),
        sa.Column('remaining_amount', sa.Numeric(18,2), nullable=False, server_default='0'),
        sa.Column('status', sa.String(30), nullable=False, server_default='pending'),
        sa.Column('expected_receive_date', sa.Date()), sa.Column('received_date', sa.Date()),
        sa.Column('note', sa.Text()), sa.Column('hold_reason', sa.Text()), sa.Column('cancel_reason', sa.Text()),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('marked_received_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('cancelled_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True)), sa.Column('marked_received_at', sa.DateTime(timezone=True)), sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.UniqueConstraint('contract_id', name='uq_company_commission_receivables_contract_id'))
    op.create_index('ix_company_commission_receivables_code','company_commission_receivables',['receivable_code'])
    op.create_index('ix_company_commission_receivables_status','company_commission_receivables',['status'])
    op.create_index('ix_company_commission_receivables_created_at','company_commission_receivables',['created_at'])
    op.create_table('company_commission_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('receivable_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_commission_receivables.id'), nullable=False),
        sa.Column('event_type', sa.String(30), nullable=False), sa.Column('from_status', sa.String(30)), sa.Column('to_status', sa.String(30)),
        sa.Column('amount', sa.Numeric(18,2)), sa.Column('note', sa.Text()), sa.Column('reason', sa.Text()),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_company_commission_events_receivable_id','company_commission_events',['receivable_id'])
    op.create_index('ix_company_commission_events_created_at','company_commission_events',['created_at'])

def downgrade():
    op.drop_table('company_commission_events'); op.drop_table('company_commission_receivables')
    for c in ['brokerage_policy_note','brokerage_contract_code','commission_payer_name','commission_payer_type','actual_seller_name','actual_seller_type','company_role']:
        op.drop_column('contracts', c)
