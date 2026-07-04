"""Sprint 27 audit logs

Revision ID: 20260704_0019
Revises: 20260703_0018
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260704_0019'
down_revision = '20260703_0018'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('actor_name', sa.String(length=255), nullable=True),
        sa.Column('actor_email', sa.String(length=255), nullable=True),
        sa.Column('action', sa.String(length=120), nullable=False),
        sa.Column('module', sa.String(length=120), nullable=False),
        sa.Column('entity_type', sa.String(length=120), nullable=False),
        sa.Column('entity_id', sa.String(length=120), nullable=False),
        sa.Column('entity_label', sa.String(length=255), nullable=True),
        sa.Column('before_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('after_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('changed_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=120), nullable=True),
        sa.Column('ip_address', sa.String(length=100), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for name, cols in {
        'ix_audit_logs_created_at':['created_at'], 'ix_audit_logs_actor_id':['actor_id'], 'ix_audit_logs_module':['module'],
        'ix_audit_logs_entity_type':['entity_type'], 'ix_audit_logs_entity_id':['entity_id'], 'ix_audit_logs_action':['action'],
        'ix_audit_logs_module_entity':['module','entity_type','entity_id'], 'ix_audit_logs_created_at_module':['created_at','module'],
    }.items(): op.create_index(name, 'audit_logs', cols)

def downgrade():
    op.drop_table('audit_logs')
