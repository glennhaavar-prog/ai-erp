"""Add bank_connections table for DNB integration (clean)

Revision ID: 20260210_0900
Revises: 20260209213000
Create Date: 2026-02-10 09:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '20260210_0900'
down_revision = '20260209213000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create bank_connections table
    op.create_table(
        'bank_connections',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('bank_name', sa.String(length=100), nullable=False),
        sa.Column('bank_account_number', sa.String(length=50), nullable=False),
        sa.Column('bank_account_id', sa.String(length=255), nullable=False),
        sa.Column('account_name', sa.String(length=255), nullable=True),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scope', sa.String(length=500), nullable=True),
        sa.Column('token_type', sa.String(length=50), nullable=True),
        sa.Column('auto_sync_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sync_frequency_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_status', sa.String(length=50), nullable=True),
        sa.Column('last_sync_error', sa.Text(), nullable=True),
        sa.Column('total_transactions_imported', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('oldest_transaction_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('newest_transaction_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('connection_status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_bank_connections_client_id', 'bank_connections', ['client_id'])
    op.create_index('ix_bank_connections_is_active', 'bank_connections', ['is_active'])
    op.create_index('ix_bank_connections_auto_sync', 'bank_connections', ['auto_sync_enabled', 'is_active'])
    op.create_index('ix_bank_connections_last_sync', 'bank_connections', ['last_sync_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_bank_connections_last_sync', table_name='bank_connections')
    op.drop_index('ix_bank_connections_auto_sync', table_name='bank_connections')
    op.drop_index('ix_bank_connections_is_active', table_name='bank_connections')
    op.drop_index('ix_bank_connections_client_id', table_name='bank_connections')
    
    # Drop table
    op.drop_table('bank_connections')
