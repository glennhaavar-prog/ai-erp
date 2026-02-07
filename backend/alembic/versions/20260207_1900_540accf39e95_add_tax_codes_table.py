"""add_tax_codes_table

Revision ID: 540accf39e95
Revises: add_accounting_schema_001
Create Date: 2026-02-07 19:00:20.700729

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '540accf39e95'
down_revision = 'add_accounting_schema_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tax_codes table
    op.create_table(
        'tax_codes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(10), nullable=False),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('direction', sa.String(20), nullable=False),  # outgoing/incoming
        sa.Column('account_number', sa.String(10), nullable=True),  # Default GL account
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('country_code', sa.String(2), nullable=False, server_default='NO'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'country_code', name='uq_tax_code_country')
    )
    
    # Create index on code for fast lookups
    op.create_index('ix_tax_codes_code', 'tax_codes', ['code'])
    
    # Seed Norwegian MVA codes (from kontali-accounting skill section 1.5)
    from sqlalchemy import table, column
    from sqlalchemy.sql import insert
    import uuid
    
    tax_codes = table('tax_codes',
        column('id'),
        column('code'),
        column('description'),
        column('rate'),
        column('direction'),
        column('account_number'),
        column('country_code')
    )
    
    norwegian_mva_codes = [
        # Outgoing VAT (sales)
        {'id': str(uuid.uuid4()), 'code': '1', 'description': '25% utgående MVA (salg)', 'rate': 25.00, 'direction': 'outgoing', 'account_number': '2700', 'country_code': 'NO'},
        {'id': str(uuid.uuid4()), 'code': '3', 'description': '15% utgående MVA (mat)', 'rate': 15.00, 'direction': 'outgoing', 'account_number': '2700', 'country_code': 'NO'},
        {'id': str(uuid.uuid4()), 'code': '5', 'description': 'Unntatt MVA (0%)', 'rate': 0.00, 'direction': 'outgoing', 'account_number': None, 'country_code': 'NO'},
        {'id': str(uuid.uuid4()), 'code': '6', 'description': 'Utenfor MVA-området (0%)', 'rate': 0.00, 'direction': 'outgoing', 'account_number': None, 'country_code': 'NO'},
        
        # Incoming VAT (purchases)
        {'id': str(uuid.uuid4()), 'code': '11', 'description': '25% inngående MVA (kjøp)', 'rate': 25.00, 'direction': 'incoming', 'account_number': '2740', 'country_code': 'NO'},
        {'id': str(uuid.uuid4()), 'code': '13', 'description': '15% inngående MVA (mat kjøp)', 'rate': 15.00, 'direction': 'incoming', 'account_number': '2740', 'country_code': 'NO'},
        {'id': str(uuid.uuid4()), 'code': '31', 'description': '25% inngående MVA (kjøp fra utlandet)', 'rate': 25.00, 'direction': 'incoming', 'account_number': '2740', 'country_code': 'NO'},
        {'id': str(uuid.uuid4()), 'code': '33', 'description': '15% inngående MVA (mat fra utlandet)', 'rate': 15.00, 'direction': 'incoming', 'account_number': '2740', 'country_code': 'NO'},
    ]
    
    op.bulk_insert(tax_codes, norwegian_mva_codes)


def downgrade() -> None:
    op.drop_index('ix_tax_codes_code', table_name='tax_codes')
    op.drop_table('tax_codes')
