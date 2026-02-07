"""add_accruals_tables

Revision ID: ac4841a7c8ad
Revises: 1a41756c4719
Create Date: 2026-02-07 21:07:33.398840

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'ac4841a7c8ad'
down_revision = '1a41756c4719'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create accruals table
    op.create_table(
        'accruals',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        
        # Description
        sa.Column('description', sa.Text, nullable=False),
        
        # Time period
        sa.Column('from_date', sa.Date, nullable=False),
        sa.Column('to_date', sa.Date, nullable=False),
        
        # Amounts
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        
        # Accounts (NS 4102)
        sa.Column('balance_account', sa.String(10), nullable=False),
        sa.Column('result_account', sa.String(10), nullable=False),
        
        # Posting schedule
        sa.Column('frequency', sa.String(20), nullable=False),
        sa.Column('next_posting_date', sa.Date),
        
        # AI features
        sa.Column('auto_post', sa.Boolean, server_default='true'),
        sa.Column('ai_detected', sa.Boolean, server_default='false'),
        sa.Column('source_invoice_id', UUID(as_uuid=True), sa.ForeignKey('vendor_invoices.id')),
        
        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_by', sa.String(20), nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp()),
        
        # Constraints
        sa.CheckConstraint('to_date >= from_date', name='check_dates'),
        sa.CheckConstraint('total_amount > 0', name='check_amount')
    )
    
    # Create indexes for accruals
    op.create_index('idx_accruals_client', 'accruals', ['client_id'])
    op.create_index('idx_accruals_status', 'accruals', ['status'])
    op.create_index('idx_accruals_next_posting', 'accruals', ['next_posting_date'], 
                    postgresql_where=sa.text("status = 'active'"))
    
    # Create accrual_postings table
    op.create_table(
        'accrual_postings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('accrual_id', UUID(as_uuid=True), sa.ForeignKey('accruals.id', ondelete='CASCADE'), nullable=False),
        
        # Posting details
        sa.Column('posting_date', sa.Date, nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('period', sa.String(7), nullable=False),
        
        # Link to general ledger
        sa.Column('general_ledger_id', UUID(as_uuid=True), sa.ForeignKey('general_ledger.id', ondelete='SET NULL')),
        
        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('posted_by', sa.String(20)),
        sa.Column('posted_at', sa.TIMESTAMP),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp()),
        
        # Constraints
        sa.CheckConstraint('amount > 0', name='check_posting_amount')
    )
    
    # Create indexes for accrual_postings
    op.create_index('idx_accrual_postings_accrual', 'accrual_postings', ['accrual_id'])
    op.create_index('idx_accrual_postings_date', 'accrual_postings', ['posting_date'])
    op.create_index('idx_accrual_postings_status', 'accrual_postings', ['status'])
    op.create_index('idx_accrual_postings_gl', 'accrual_postings', ['general_ledger_id'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_accrual_postings_gl', table_name='accrual_postings')
    op.drop_index('idx_accrual_postings_status', table_name='accrual_postings')
    op.drop_index('idx_accrual_postings_date', table_name='accrual_postings')
    op.drop_index('idx_accrual_postings_accrual', table_name='accrual_postings')
    
    op.drop_index('idx_accruals_next_posting', table_name='accruals')
    op.drop_index('idx_accruals_status', table_name='accruals')
    op.drop_index('idx_accruals_client', table_name='accruals')
    
    # Drop tables
    op.drop_table('accrual_postings')
    op.drop_table('accruals')
