"""add_tax_code_fk_to_general_ledger_lines

Revision ID: 1a41756c4719
Revises: 540accf39e95
Create Date: 2026-02-07 19:01:05.706971

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a41756c4719'
down_revision = '540accf39e95'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tax_code_id FK to general_ledger_lines (nullable for backward compatibility)
    op.add_column(
        'general_ledger_lines',
        sa.Column('tax_code_id', sa.UUID(), nullable=True)
    )
    
    # Create FK constraint
    op.create_foreign_key(
        'fk_general_ledger_lines_tax_code',
        'general_ledger_lines',
        'tax_codes',
        ['tax_code_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for fast lookups
    op.create_index(
        'ix_general_ledger_lines_tax_code_id',
        'general_ledger_lines',
        ['tax_code_id']
    )


def downgrade() -> None:
    op.drop_index('ix_general_ledger_lines_tax_code_id', table_name='general_ledger_lines')
    op.drop_constraint('fk_general_ledger_lines_tax_code', 'general_ledger_lines', type_='foreignkey')
    op.drop_column('general_ledger_lines', 'tax_code_id')
