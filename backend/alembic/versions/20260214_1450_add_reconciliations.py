"""add_reconciliations_and_attachments

Revision ID: 20260214_1450
Revises: 20260214_1336
Create Date: 2026-02-14 14:50:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20260214_1450'
down_revision = '7f8e9d1c2b3a'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add reconciliations and reconciliation_attachments tables
    """
    
    # Create reconciliations table
    op.create_table(
        'reconciliations',
        # Primary Key
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # Foreign Keys
        sa.Column('client_id', UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', UUID(as_uuid=True), nullable=False),
        
        # Period
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        
        # Balances
        sa.Column('opening_balance', sa.Numeric(15, 2), nullable=False),
        sa.Column('closing_balance', sa.Numeric(15, 2), nullable=False),
        sa.Column('expected_balance', sa.Numeric(15, 2), nullable=True),
        sa.Column('difference', sa.Numeric(15, 2), nullable=True),
        
        # Classification
        sa.Column('status', sa.Enum('pending', 'reconciled', 'approved', name='reconciliationstatus'), 
                  nullable=False, server_default='pending'),
        sa.Column('reconciliation_type', sa.Enum('bank', 'receivables', 'payables', 'inventory', 'other', 
                  name='reconciliationtype'), nullable=False),
        
        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Timestamps and User Tracking
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('reconciled_at', sa.DateTime(), nullable=True),
        sa.Column('reconciled_by', UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', UUID(as_uuid=True), nullable=True),
        
        # Foreign Key Constraints
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['chart_of_accounts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['reconciled_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for fast lookups
    op.create_index('idx_reconciliations_client_id', 'reconciliations', ['client_id'])
    op.create_index('idx_reconciliations_account_id', 'reconciliations', ['account_id'])
    op.create_index('idx_reconciliations_period_start', 'reconciliations', ['period_start'])
    op.create_index('idx_reconciliations_period_end', 'reconciliations', ['period_end'])
    op.create_index('idx_reconciliations_status', 'reconciliations', ['status'])
    op.create_index('idx_reconciliations_type', 'reconciliations', ['reconciliation_type'])
    
    # Create reconciliation_attachments table
    op.create_table(
        'reconciliation_attachments',
        # Primary Key
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # Foreign Key
        sa.Column('reconciliation_id', UUID(as_uuid=True), nullable=False),
        
        # File Information
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('file_size', sa.Numeric(15, 0), nullable=True),
        
        # Upload Tracking
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('uploaded_by', UUID(as_uuid=True), nullable=True),
        
        # Foreign Key Constraints
        sa.ForeignKeyConstraint(['reconciliation_id'], ['reconciliations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Create index
    op.create_index('idx_reconciliation_attachments_reconciliation_id', 
                    'reconciliation_attachments', ['reconciliation_id'])


def downgrade():
    """
    Remove reconciliations and reconciliation_attachments tables
    """
    
    # Drop indexes
    op.drop_index('idx_reconciliation_attachments_reconciliation_id', 'reconciliation_attachments')
    
    # Drop reconciliation_attachments table
    op.drop_table('reconciliation_attachments')
    
    # Drop indexes
    op.drop_index('idx_reconciliations_type', 'reconciliations')
    op.drop_index('idx_reconciliations_status', 'reconciliations')
    op.drop_index('idx_reconciliations_period_end', 'reconciliations')
    op.drop_index('idx_reconciliations_period_start', 'reconciliations')
    op.drop_index('idx_reconciliations_account_id', 'reconciliations')
    op.drop_index('idx_reconciliations_client_id', 'reconciliations')
    
    # Drop reconciliations table
    op.drop_table('reconciliations')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS reconciliationstatus')
    op.execute('DROP TYPE IF EXISTS reconciliationtype')
