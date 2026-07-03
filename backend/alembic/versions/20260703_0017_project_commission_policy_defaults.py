"""project commission policy defaults

Revision ID: 20260703_0017
Revises: 20260703_0016
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = "20260703_0017"
down_revision = "20260703_0016"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('sales_commission_payout_policy_default', sa.String(50), nullable=True))
    op.add_column('projects', sa.Column('sales_commission_policy_note', sa.Text(), nullable=True))
    op.add_column('projects', sa.Column('company_commission_policy_note', sa.Text(), nullable=True))
    op.add_column('sales_commissions', sa.Column('payout_policy_code', sa.String(50), nullable=True))
    op.add_column('sales_commissions', sa.Column('payout_policy_source', sa.String(50), nullable=True))


def downgrade():
    op.drop_column('sales_commissions', 'payout_policy_source')
    op.drop_column('sales_commissions', 'payout_policy_code')
    op.drop_column('projects', 'company_commission_policy_note')
    op.drop_column('projects', 'sales_commission_policy_note')
    op.drop_column('projects', 'sales_commission_payout_policy_default')
