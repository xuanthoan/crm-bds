"""payment management sprint 16

Revision ID: 20260625_0012
Revises: 20260623_0011
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='20260625_0012'
down_revision='20260623_0011'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('payment_schedules',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('payment_code',sa.String(30),nullable=False),sa.Column('contract_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('contracts.id'),nullable=False),sa.Column('deal_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('deals.id')),sa.Column('customer_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('customers.id')),sa.Column('property_unit_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('property_units.id')),sa.Column('sequence_no',sa.Integer(),nullable=False),sa.Column('title',sa.String(255),nullable=False),sa.Column('due_date',sa.Date(),nullable=False),sa.Column('expected_amount',sa.Numeric(18,2),nullable=False),sa.Column('paid_amount',sa.Numeric(18,2),nullable=False,server_default='0'),sa.Column('remaining_amount',sa.Numeric(18,2),nullable=False),sa.Column('penalty_amount',sa.Numeric(18,2),nullable=False,server_default='0'),sa.Column('penalty_reason',sa.Text()),sa.Column('penalty_applied_at',sa.DateTime(timezone=True)),sa.Column('status',sa.String(30),nullable=False,server_default='pending'),sa.Column('payment_method',sa.String(50)),sa.Column('note',sa.Text()),sa.Column('created_by_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id'),nullable=False),sa.Column('updated_by_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id')),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.Column('deleted_at',sa.DateTime(timezone=True)),sa.UniqueConstraint('contract_id','sequence_no',name='uq_payment_schedules_contract_sequence'))
    op.create_index('ix_payment_schedules_contract_id','payment_schedules',['contract_id'])
    op.create_index('ix_payment_schedules_deal_id','payment_schedules',['deal_id'])
    op.create_index('ix_payment_schedules_customer_id','payment_schedules',['customer_id'])
    op.create_index('ix_payment_schedules_status','payment_schedules',['status'])
    op.create_index('ix_payment_schedules_due_date','payment_schedules',['due_date'])
    op.create_index('ix_payment_schedules_payment_code','payment_schedules',['payment_code'])
    op.create_table('payment_receipts',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('receipt_code',sa.String(30),nullable=False,unique=True),sa.Column('payment_schedule_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('payment_schedules.id'),nullable=False),sa.Column('contract_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('contracts.id'),nullable=False),sa.Column('deal_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('deals.id')),sa.Column('customer_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('customers.id')),sa.Column('amount',sa.Numeric(18,2),nullable=False),sa.Column('payment_date',sa.Date()),sa.Column('payment_method',sa.String(50)),sa.Column('reference_no',sa.String(100)),sa.Column('received_by_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id')),sa.Column('note',sa.Text()),sa.Column('status',sa.String(30),nullable=False,server_default='draft'),sa.Column('created_by_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id'),nullable=False),sa.Column('updated_by_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id')),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.Column('deleted_at',sa.DateTime(timezone=True)))
    op.create_index('ix_payment_receipts_payment_schedule_id','payment_receipts',['payment_schedule_id']); op.create_index('ix_payment_receipts_receipt_code','payment_receipts',['receipt_code'])
    op.create_table('payment_invoices',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('invoice_code',sa.String(30),nullable=False,unique=True),sa.Column('contract_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('contracts.id'),nullable=False),sa.Column('payment_schedule_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('payment_schedules.id')),sa.Column('customer_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('customers.id')),sa.Column('amount',sa.Numeric(18,2),nullable=False),sa.Column('issued_date',sa.Date(),nullable=False),sa.Column('status',sa.String(30),nullable=False,server_default='draft'),sa.Column('note',sa.Text()),sa.Column('created_by_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id'),nullable=False),sa.Column('updated_by_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id')),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.Column('deleted_at',sa.DateTime(timezone=True)))
    for c in ('contract_id','payment_schedule_id','invoice_code'): op.create_index(f'ix_payment_invoices_{c}','payment_invoices',[c])
def downgrade():
    op.drop_table('payment_invoices'); op.drop_table('payment_receipts'); op.drop_table('payment_schedules')
