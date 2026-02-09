"""Add bank_reconciliations table

Revision ID: 20260208133000
Revises: ac4841a7c8ad
Create Date: 2026-02-08 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260208133000'
down_revision = 'ac4841a7c8ad'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types (if not exists)
    connection = op.get_bind()
    connection.execute(sa.text("DO $$ BEGIN CREATE TYPE matchtype AS ENUM ('auto', 'manual', 'suggested'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
    connection.execute(sa.text("DO $$ BEGIN CREATE TYPE matchstatus AS ENUM ('pending', 'approved', 'rejected'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
    connection.commit()
    
    # Create bank_reconciliations table
    op.create_table('bank_reconciliations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_invoice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('customer_invoice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('match_type', postgresql.ENUM('auto', 'manual', 'suggested', name='matchtype', create_type=False), nullable=False),
        sa.Column('match_status', postgresql.ENUM('pending', 'approved', 'rejected', name='matchstatus', create_type=False), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('match_reason', sa.Text(), nullable=True),
        sa.Column('match_criteria', sa.Text(), nullable=True),
        sa.Column('transaction_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('voucher_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('amount_difference', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('matched_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('matched_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['bank_transactions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_invoice_id'], ['vendor_invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_invoice_id'], ['customer_invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['voucher_id'], ['general_ledger.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['matched_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rejected_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_bank_reconciliations_client_id'), 'bank_reconciliations', ['client_id'], unique=False)
    op.create_index(op.f('ix_bank_reconciliations_transaction_id'), 'bank_reconciliations', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_bank_reconciliations_vendor_invoice_id'), 'bank_reconciliations', ['vendor_invoice_id'], unique=False)
    op.create_index(op.f('ix_bank_reconciliations_customer_invoice_id'), 'bank_reconciliations', ['customer_invoice_id'], unique=False)
    op.create_index(op.f('ix_bank_reconciliations_voucher_id'), 'bank_reconciliations', ['voucher_id'], unique=False)
    op.create_index(op.f('ix_bank_reconciliations_match_type'), 'bank_reconciliations', ['match_type'], unique=False)
    op.create_index(op.f('ix_bank_reconciliations_match_status'), 'bank_reconciliations', ['match_status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_bank_reconciliations_match_status'), table_name='bank_reconciliations')
    op.drop_index(op.f('ix_bank_reconciliations_match_type'), table_name='bank_reconciliations')
    op.drop_index(op.f('ix_bank_reconciliations_voucher_id'), table_name='bank_reconciliations')
    op.drop_index(op.f('ix_bank_reconciliations_customer_invoice_id'), table_name='bank_reconciliations')
    op.drop_index(op.f('ix_bank_reconciliations_vendor_invoice_id'), table_name='bank_reconciliations')
    op.drop_index(op.f('ix_bank_reconciliations_transaction_id'), table_name='bank_reconciliations')
    op.drop_index(op.f('ix_bank_reconciliations_client_id'), table_name='bank_reconciliations')
    
    # Drop table
    op.drop_table('bank_reconciliations')
    
    # Drop enum types
    connection = op.get_bind()
    connection.execute(sa.text("DROP TYPE IF EXISTS matchstatus"))
    connection.execute(sa.text("DROP TYPE IF EXISTS matchtype"))
    connection.commit()
