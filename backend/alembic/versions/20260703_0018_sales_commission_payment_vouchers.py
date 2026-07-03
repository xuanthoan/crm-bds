"""sales commission payment vouchers

Revision ID: 20260703_0018
Revises: 20260703_0017
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision='20260703_0018'
down_revision='20260703_0017'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('sales_commissions', sa.Column('legacy_paid_amount', sa.Numeric(18,2), nullable=False, server_default='0'))
    op.execute('UPDATE sales_commissions SET legacy_paid_amount = COALESCE(paid_amount, 0)')
    op.create_table('sales_commission_payment_vouchers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('code', sa.String(40), nullable=False),
        sa.Column('sales_commission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sales_commissions.id'), nullable=False),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contracts.id')),
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('amount', sa.Numeric(18,2), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('payment_method', sa.String(30), nullable=False),
        sa.Column('payment_reference', sa.String(255)),
        sa.Column('status', sa.String(30), nullable=False, server_default='draft'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('paid_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('cancelled_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('paid_at', sa.DateTime(timezone=True)), sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.Column('cancel_reason', sa.Text()), sa.Column('note', sa.Text()), sa.Column('attachment_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('code', name='uq_sales_commission_payment_vouchers_code'),
        sa.CheckConstraint('amount > 0', name='ck_sales_commission_payment_vouchers_amount_positive'))
    for name,col in [('ix_scpv_sales_commission_id','sales_commission_id'),('ix_scpv_contract_id','contract_id'),('ix_scpv_sale_id','sale_id'),('ix_scpv_status','status'),('ix_scpv_payment_date','payment_date')]: op.create_index(name,'sales_commission_payment_vouchers',[col])

def downgrade():
    op.drop_table('sales_commission_payment_vouchers')
    op.drop_column('sales_commissions','legacy_paid_amount')
