"""add_opening_balance_tables

Revision ID: 20260211_1016_add_opening_balance
Revises: 20260211_1010_add_client_settings
Create Date: 2026-02-11 10:16:00

Adds tables for Opening Balance Import (Åpningsbalanse):
- opening_balances: Import session tracking
- opening_balance_lines: Individual account balances

Critical validations:
1. SUM(debit) MUST = SUM(credit) - no exceptions
2. Bank accounts MUST match actual bank balance
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20260211_1016'
down_revision = '20260211_1010'
branch_labels = None
depends_on = None


def upgrade():
    """Create opening balance tables"""
    
    # 1. Create opening_balances table
    op.create_table(
        'opening_balances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('import_date', sa.Date(), nullable=False),
        sa.Column('fiscal_year', sa.String(4), nullable=False),
        sa.Column('description', sa.Text(), server_default='Åpningsbalanse', nullable=False),
        sa.Column('status', sa.String(50), server_default='draft', nullable=False),
        
        # Validation results
        sa.Column('is_balanced', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('balance_difference', sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column('bank_balance_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('bank_balance_errors', JSONB, nullable=True),
        sa.Column('missing_accounts', JSONB, nullable=True),
        sa.Column('validation_errors', JSONB, nullable=True),
        
        # Cached totals
        sa.Column('total_debit', sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column('total_credit', sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column('line_count', sa.Integer(), server_default='0', nullable=False),
        
        # Upload metadata
        sa.Column('original_filename', sa.String(255), nullable=True),
        sa.Column('uploaded_by_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        
        # Import result
        sa.Column('imported_at', sa.DateTime(), nullable=True),
        sa.Column('journal_entry_id', UUID(as_uuid=True), sa.ForeignKey('general_ledger.id', ondelete='SET NULL'), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), onupdate=datetime.utcnow, nullable=False),
    )
    
    # Indexes for opening_balances
    op.create_index('idx_opening_balances_client', 'opening_balances', ['client_id'])
    op.create_index('idx_opening_balances_status', 'opening_balances', ['status'])
    op.create_index('idx_opening_balances_fiscal_year', 'opening_balances', ['fiscal_year'])
    op.create_index('idx_opening_balances_import_date', 'opening_balances', ['import_date'])
    
    # 2. Create opening_balance_lines table
    op.create_table(
        'opening_balance_lines',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('opening_balance_id', UUID(as_uuid=True), sa.ForeignKey('opening_balances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('account_number', sa.String(10), nullable=False),
        sa.Column('account_name', sa.String(255), nullable=False),
        
        # Amounts
        sa.Column('debit_amount', sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column('credit_amount', sa.Numeric(15, 2), server_default='0', nullable=False),
        
        # Validation
        sa.Column('account_exists', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_bank_account', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('bank_balance_match', sa.Boolean(), nullable=True),
        sa.Column('expected_bank_balance', sa.Numeric(15, 2), nullable=True),
        sa.Column('validation_errors', JSONB, nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Indexes for opening_balance_lines
    op.create_index('idx_opening_balance_lines_ob', 'opening_balance_lines', ['opening_balance_id'])
    op.create_index('idx_opening_balance_lines_account', 'opening_balance_lines', ['account_number'])
    
    # Unique constraint on opening_balance_id + line_number
    op.create_unique_constraint(
        'uq_opening_balance_line_number',
        'opening_balance_lines',
        ['opening_balance_id', 'line_number']
    )


def downgrade():
    """Remove opening balance tables"""
    
    # Drop in reverse order
    op.drop_constraint('uq_opening_balance_line_number', 'opening_balance_lines', type_='unique')
    op.drop_index('idx_opening_balance_lines_account', 'opening_balance_lines')
    op.drop_index('idx_opening_balance_lines_ob', 'opening_balance_lines')
    op.drop_table('opening_balance_lines')
    
    op.drop_index('idx_opening_balances_import_date', 'opening_balances')
    op.drop_index('idx_opening_balances_fiscal_year', 'opening_balances')
    op.drop_index('idx_opening_balances_status', 'opening_balances')
    op.drop_index('idx_opening_balances_client', 'opening_balances')
    op.drop_table('opening_balances')
