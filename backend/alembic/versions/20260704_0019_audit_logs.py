"""Sprint 27 audit logs

Revision ID: 20260704_0019
Revises: 20260703_0018
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = '20260704_0019'
down_revision = '20260703_0018'
branch_labels = None
depends_on = None

TABLE_NAME = 'audit_logs'

COLUMN_DEFINITIONS = {
    'id': sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
    'actor_id': sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    'user_id': sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    'actor_name': sa.Column('actor_name', sa.String(length=255), nullable=True),
    'actor_email': sa.Column('actor_email', sa.String(length=255), nullable=True),
    'action': sa.Column('action', sa.String(length=120), nullable=False),
    'module': sa.Column('module', sa.String(length=120), nullable=False),
    'entity_type': sa.Column('entity_type', sa.String(length=120), nullable=False),
    'entity_id': sa.Column('entity_id', sa.String(length=120), nullable=False),
    'entity_label': sa.Column('entity_label', sa.String(length=255), nullable=True),
    'before_data': sa.Column('before_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    'after_data': sa.Column('after_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    'changed_fields': sa.Column('changed_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    'description': sa.Column('description', sa.Text(), nullable=True),
    'reason': sa.Column('reason', sa.Text(), nullable=True),
    'request_id': sa.Column('request_id', sa.String(length=120), nullable=True),
    'ip_address': sa.Column('ip_address', sa.String(length=100), nullable=True),
    'user_agent': sa.Column('user_agent', sa.Text(), nullable=True),
    'created_at': sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
}

INDEX_DEFINITIONS = {
    'ix_audit_logs_created_at': ['created_at'],
    'ix_audit_logs_actor_id': ['actor_id'],
    'ix_audit_logs_module': ['module'],
    'ix_audit_logs_entity_type': ['entity_type'],
    'ix_audit_logs_entity_id': ['entity_id'],
    'ix_audit_logs_action': ['action'],
    'ix_audit_logs_module_entity': ['module', 'entity_type', 'entity_id'],
    'ix_audit_logs_created_at_module': ['created_at', 'module'],
}


def _inspector():
    return inspect(op.get_bind())


def _table_exists() -> bool:
    return TABLE_NAME in _inspector().get_table_names()


def _existing_columns() -> set[str]:
    return {column['name'] for column in _inspector().get_columns(TABLE_NAME)} if _table_exists() else set()


def _existing_indexes() -> set[str]:
    return {index['name'] for index in _inspector().get_indexes(TABLE_NAME)} if _table_exists() else set()


def _create_missing_columns() -> None:
    existing_columns = _existing_columns()
    for name, column in COLUMN_DEFINITIONS.items():
        if name == 'id':
            continue
        if name not in existing_columns:
            op.add_column(TABLE_NAME, column.copy())


def _create_missing_indexes() -> None:
    existing_indexes = _existing_indexes()
    existing_columns = _existing_columns()
    for name, columns in INDEX_DEFINITIONS.items():
        if name not in existing_indexes and all(column in existing_columns for column in columns):
            op.create_index(name, TABLE_NAME, columns)


def upgrade():
    if not _table_exists():
        op.create_table(TABLE_NAME, *[column.copy() for column in COLUMN_DEFINITIONS.values()])
    else:
        _create_missing_columns()
    _create_missing_indexes()


def downgrade():
    if not _table_exists():
        return
    for name in reversed(list(INDEX_DEFINITIONS)):
        if name in _existing_indexes():
            op.drop_index(name, table_name=TABLE_NAME)
    if _table_exists():
        op.drop_table(TABLE_NAME)
