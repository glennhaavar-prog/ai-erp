"""add_currency_rates_and_multi_currency_support

Revision ID: 20260211_1310
Revises: 20260211_1025_add_contact_register
Create Date: 2026-02-11 13:10:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20260211_1310'
down_revision = '20260211_1025'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add currency_rates table and multi-currency support to client_settings
    """
    
    # Create currency_rates table
    op.create_table(
        'currency_rates',
        # Primary Key
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # Currency Information
        sa.Column('currency_code', sa.String(10), nullable=False),
        sa.Column('base_currency', sa.String(3), nullable=False, server_default='NOK'),
        
        # Rate (how many NOK for 1 unit of currency_code)
        sa.Column('rate', sa.Numeric(20, 6), nullable=False),
        
        # Date this rate applies to
        sa.Column('rate_date', sa.Date(), nullable=False, server_default=sa.text('CURRENT_DATE')),
        
        # Source of the rate
        sa.Column('source', sa.String(50), nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for fast lookups
    op.create_index('idx_currency_rates_currency_code', 'currency_rates', ['currency_code'])
    op.create_index('idx_currency_rates_rate_date', 'currency_rates', ['rate_date'])
    op.create_index('idx_currency_date', 'currency_rates', ['currency_code', 'rate_date'])
    op.create_index('idx_date_currency', 'currency_rates', ['rate_date', 'currency_code'])
    
    # Add multi-currency support columns to client_settings
    op.add_column('client_settings', 
        sa.Column('supported_currencies', sa.JSON(), nullable=False, server_default='["NOK"]')
    )
    op.add_column('client_settings', 
        sa.Column('auto_update_rates', sa.Boolean(), nullable=False, server_default='true')
    )
    op.add_column('client_settings', 
        sa.Column('last_rate_update', sa.DateTime(), nullable=True)
    )


def downgrade():
    """
    Remove currency_rates table and multi-currency support
    """
    
    # Remove columns from client_settings
    op.drop_column('client_settings', 'last_rate_update')
    op.drop_column('client_settings', 'auto_update_rates')
    op.drop_column('client_settings', 'supported_currencies')
    
    # Drop indexes
    op.drop_index('idx_date_currency', 'currency_rates')
    op.drop_index('idx_currency_date', 'currency_rates')
    op.drop_index('idx_currency_rates_rate_date', 'currency_rates')
    op.drop_index('idx_currency_rates_currency_code', 'currency_rates')
    
    # Drop table
    op.drop_table('currency_rates')
