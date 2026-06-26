"""receipt invoice contract completion

Revision ID: 20260626_0013
Revises: 20260625_0012
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260626_0013'
down_revision = '20260625_0012'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('payment_receipts', sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('payment_receipts', sa.Column('confirmed_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('payment_receipts', sa.Column('cancel_reason', sa.Text(), nullable=True))
    op.add_column('payment_receipts', sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('payment_receipts', sa.Column('cancelled_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_payment_receipts_confirmed_by_id_users', 'payment_receipts', 'users', ['confirmed_by_id'], ['id'])
    op.create_foreign_key('fk_payment_receipts_cancelled_by_id_users', 'payment_receipts', 'users', ['cancelled_by_id'], ['id'])
    op.add_column('payment_invoices', sa.Column('receipt_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('payment_invoices', sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('payment_invoices', sa.Column('property_unit_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('payment_invoices', sa.Column('due_date', sa.Date(), nullable=True))
    op.add_column('payment_invoices', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('payment_invoices', sa.Column('cancel_reason', sa.Text(), nullable=True))
    op.add_column('payment_invoices', sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('payment_invoices', sa.Column('issued_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('payment_invoices', sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('payment_invoices', sa.Column('cancelled_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.alter_column('payment_invoices', 'issued_date', existing_type=sa.Date(), nullable=True)
    op.create_foreign_key('fk_payment_invoices_receipt_id_receipts', 'payment_invoices', 'payment_receipts', ['receipt_id'], ['id'])
    op.create_foreign_key('fk_payment_invoices_deal_id_deals', 'payment_invoices', 'deals', ['deal_id'], ['id'])
    op.create_foreign_key('fk_payment_invoices_property_unit_id_property_units', 'payment_invoices', 'property_units', ['property_unit_id'], ['id'])
    op.create_foreign_key('fk_payment_invoices_issued_by_id_users', 'payment_invoices', 'users', ['issued_by_id'], ['id'])
    op.create_foreign_key('fk_payment_invoices_cancelled_by_id_users', 'payment_invoices', 'users', ['cancelled_by_id'], ['id'])

def downgrade():
    pass
