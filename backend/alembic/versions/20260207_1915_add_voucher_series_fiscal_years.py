"""add voucher_series, fiscal_years, accounting_periods tables

Revision ID: add_accounting_schema_001
Revises: add_demo_flags_001
Create Date: 2026-02-07 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'add_accounting_schema_001'
down_revision: Union[str, None] = 'add_demo_flags_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create voucher_series, fiscal_years, accounting_periods tables and add FKs to general_ledger"""

    # 1. Create voucher_series table
    op.create_table(
        'voucher_series',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(10), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('next_number', sa.Integer(), server_default='1'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('client_id', 'code', name='uq_voucher_series_client_code'),
    )
    op.create_index('idx_voucher_series_client', 'voucher_series', ['client_id'])

    # 2. Create fiscal_years table
    op.create_table(
        'fiscal_years',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_closed', sa.Boolean(), server_default='false'),
        sa.Column('is_locked', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('client_id', 'year', name='uq_fiscal_years_client_year'),
    )
    op.create_index('idx_fiscal_years_client', 'fiscal_years', ['client_id'])

    # 3. Create accounting_periods table
    op.create_table(
        'accounting_periods',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fiscal_year_id', UUID(as_uuid=True), sa.ForeignKey('fiscal_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_number', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_closed', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('fiscal_year_id', 'period_number', name='uq_accounting_periods_fy_number'),
    )
    op.create_index('idx_accounting_periods_fy', 'accounting_periods', ['fiscal_year_id'])

    # 4. Add FK columns to general_ledger (nullable for backward compatibility)
    op.add_column('general_ledger', sa.Column('voucher_series_id', UUID(as_uuid=True), nullable=True))
    op.add_column('general_ledger', sa.Column('fiscal_year_id', UUID(as_uuid=True), nullable=True))
    op.add_column('general_ledger', sa.Column('period_id', UUID(as_uuid=True), nullable=True))

    # Create foreign keys for general_ledger
    op.create_foreign_key(
        'fk_general_ledger_voucher_series',
        'general_ledger', 'voucher_series',
        ['voucher_series_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_general_ledger_fiscal_year',
        'general_ledger', 'fiscal_years',
        ['fiscal_year_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_general_ledger_period',
        'general_ledger', 'accounting_periods',
        ['period_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create indexes for general_ledger FK columns
    op.create_index('idx_general_ledger_vs', 'general_ledger', ['voucher_series_id'])
    op.create_index('idx_general_ledger_fy', 'general_ledger', ['fiscal_year_id'])
    op.create_index('idx_general_ledger_period', 'general_ledger', ['period_id'])


def downgrade() -> None:
    """Remove voucher_series, fiscal_years, accounting_periods tables and FK columns from general_ledger"""

    # Drop indexes from general_ledger
    op.drop_index('idx_general_ledger_period', table_name='general_ledger')
    op.drop_index('idx_general_ledger_fy', table_name='general_ledger')
    op.drop_index('idx_general_ledger_vs', table_name='general_ledger')

    # Drop foreign keys from general_ledger
    op.drop_constraint('fk_general_ledger_period', 'general_ledger', type_='foreignkey')
    op.drop_constraint('fk_general_ledger_fiscal_year', 'general_ledger', type_='foreignkey')
    op.drop_constraint('fk_general_ledger_voucher_series', 'general_ledger', type_='foreignkey')

    # Drop columns from general_ledger
    op.drop_column('general_ledger', 'period_id')
    op.drop_column('general_ledger', 'fiscal_year_id')
    op.drop_column('general_ledger', 'voucher_series_id')

    # Drop accounting_periods table
    op.drop_index('idx_accounting_periods_fy', table_name='accounting_periods')
    op.drop_table('accounting_periods')

    # Drop fiscal_years table
    op.drop_index('idx_fiscal_years_client', table_name='fiscal_years')
    op.drop_table('fiscal_years')

    # Drop voucher_series table
    op.drop_index('idx_voucher_series_client', table_name='voucher_series')
    op.drop_table('voucher_series')
