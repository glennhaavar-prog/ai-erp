"""add_subledgers_and_voucher_extensions

Revision ID: 20260209_2130_add_subledgers
Revises: 20260209_2120_add_tasks_tables
Create Date: 2026-02-09 21:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20260209213000'
down_revision = '20260209212000'
branch_labels = None
depends_on = None


def upgrade():
    """Create supplier_ledger, customer_ledger, and extend general_ledger"""
    
    # 1. Extend general_ledger table with new fields
    op.add_column('general_ledger',
        sa.Column('voucher_type', sa.String(50), nullable=True)
    )
    op.add_column('general_ledger',
        sa.Column('external_reference', sa.String(255), nullable=True)
    )
    op.add_column('general_ledger',
        sa.Column('posted_by', sa.String(100), nullable=True)
    )
    op.add_column('general_ledger',
        sa.Column('posted_at', sa.DateTime(), nullable=True)
    )
    
    # Create index on voucher_type for filtering
    op.create_index('idx_gl_voucher_type', 'general_ledger', ['voucher_type'])
    
    # 2. Create supplier_ledger table
    op.create_table(
        'supplier_ledger',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('supplier_id', UUID(as_uuid=True), sa.ForeignKey('vendors.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('voucher_id', UUID(as_uuid=True), sa.ForeignKey('general_ledger.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('remaining_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='NOK', nullable=False),
        sa.Column('status', sa.String(50), server_default='open', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), onupdate=datetime.utcnow, nullable=False),
    )
    
    # Indexes for supplier_ledger
    op.create_index('idx_supplier_ledger_client', 'supplier_ledger', ['client_id'])
    op.create_index('idx_supplier_ledger_supplier', 'supplier_ledger', ['supplier_id'])
    op.create_index('idx_supplier_ledger_status', 'supplier_ledger', ['status'])
    op.create_index('idx_supplier_ledger_due_date', 'supplier_ledger', ['due_date'])
    op.create_index('idx_supplier_ledger_invoice_date', 'supplier_ledger', ['invoice_date'])
    
    # 3. Create supplier_ledger_transactions table
    op.create_table(
        'supplier_ledger_transactions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('ledger_id', UUID(as_uuid=True), sa.ForeignKey('supplier_ledger.id', ondelete='CASCADE'), nullable=False),
        sa.Column('voucher_id', UUID(as_uuid=True), sa.ForeignKey('general_ledger.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),  # 'invoice', 'payment', 'credit_note'
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Indexes for supplier_ledger_transactions
    op.create_index('idx_supplier_ledger_trans_ledger', 'supplier_ledger_transactions', ['ledger_id'])
    op.create_index('idx_supplier_ledger_trans_date', 'supplier_ledger_transactions', ['transaction_date'])
    
    # 4. Create customer_ledger table
    op.create_table(
        'customer_ledger',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('customer_id', UUID(as_uuid=True), nullable=True),  # Can be NULL for one-time customers
        sa.Column('customer_name', sa.String(255), nullable=False),  # Denormalized for performance
        sa.Column('voucher_id', UUID(as_uuid=True), sa.ForeignKey('general_ledger.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('remaining_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='NOK', nullable=False),
        sa.Column('status', sa.String(50), server_default='open', nullable=False),
        sa.Column('kid_number', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), onupdate=datetime.utcnow, nullable=False),
    )
    
    # Indexes for customer_ledger
    op.create_index('idx_customer_ledger_client', 'customer_ledger', ['client_id'])
    op.create_index('idx_customer_ledger_customer', 'customer_ledger', ['customer_id'])
    op.create_index('idx_customer_ledger_status', 'customer_ledger', ['status'])
    op.create_index('idx_customer_ledger_kid', 'customer_ledger', ['kid_number'])
    op.create_index('idx_customer_ledger_due_date', 'customer_ledger', ['due_date'])
    op.create_index('idx_customer_ledger_invoice_date', 'customer_ledger', ['invoice_date'])
    
    # 5. Create customer_ledger_transactions table
    op.create_table(
        'customer_ledger_transactions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('ledger_id', UUID(as_uuid=True), sa.ForeignKey('customer_ledger.id', ondelete='CASCADE'), nullable=False),
        sa.Column('voucher_id', UUID(as_uuid=True), sa.ForeignKey('general_ledger.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),  # 'invoice', 'payment', 'credit_note'
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Indexes for customer_ledger_transactions
    op.create_index('idx_customer_ledger_trans_ledger', 'customer_ledger_transactions', ['ledger_id'])
    op.create_index('idx_customer_ledger_trans_date', 'customer_ledger_transactions', ['transaction_date'])


def downgrade():
    """Remove subledger tables and general_ledger extensions"""
    
    # Drop indexes and tables in reverse order
    op.drop_index('idx_customer_ledger_trans_date', 'customer_ledger_transactions')
    op.drop_index('idx_customer_ledger_trans_ledger', 'customer_ledger_transactions')
    op.drop_table('customer_ledger_transactions')
    
    op.drop_index('idx_customer_ledger_invoice_date', 'customer_ledger')
    op.drop_index('idx_customer_ledger_due_date', 'customer_ledger')
    op.drop_index('idx_customer_ledger_kid', 'customer_ledger')
    op.drop_index('idx_customer_ledger_status', 'customer_ledger')
    op.drop_index('idx_customer_ledger_customer', 'customer_ledger')
    op.drop_index('idx_customer_ledger_client', 'customer_ledger')
    op.drop_table('customer_ledger')
    
    op.drop_index('idx_supplier_ledger_trans_date', 'supplier_ledger_transactions')
    op.drop_index('idx_supplier_ledger_trans_ledger', 'supplier_ledger_transactions')
    op.drop_table('supplier_ledger_transactions')
    
    op.drop_index('idx_supplier_ledger_invoice_date', 'supplier_ledger')
    op.drop_index('idx_supplier_ledger_due_date', 'supplier_ledger')
    op.drop_index('idx_supplier_ledger_status', 'supplier_ledger')
    op.drop_index('idx_supplier_ledger_supplier', 'supplier_ledger')
    op.drop_index('idx_supplier_ledger_client', 'supplier_ledger')
    op.drop_table('supplier_ledger')
    
    op.drop_index('idx_gl_voucher_type', 'general_ledger')
    op.drop_column('general_ledger', 'posted_at')
    op.drop_column('general_ledger', 'posted_by')
    op.drop_column('general_ledger', 'external_reference')
    op.drop_column('general_ledger', 'voucher_type')
