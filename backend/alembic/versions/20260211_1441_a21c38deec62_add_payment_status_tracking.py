"""add_payment_status_tracking

Revision ID: a21c38deec62
Revises: add_ai_features
Create Date: 2026-02-11 14:41:12.844979

Adds payment status tracking to vendor_invoices and customer_invoices:
- payment_status enum with values: unpaid, partially_paid, paid, overdue
- paid_amount to track partial payments
- paid_date to record full payment date
- Proper indexes for performance
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision = 'a21c38deec62'
down_revision = 'add_ai_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payment_status enum type
    payment_status_enum = ENUM(
        'unpaid', 'partially_paid', 'paid', 'overdue',
        name='payment_status_enum',
        create_type=False
    )
    payment_status_enum.create(op.get_bind(), checkfirst=True)
    
    # === VENDOR INVOICES ===
    
    # Check if payment_status column exists and update it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    vendor_columns = [col['name'] for col in inspector.get_columns('vendor_invoices')]
    
    if 'payment_status' in vendor_columns:
        # Drop the old column if it exists
        op.drop_column('vendor_invoices', 'payment_status')
    
    # Add payment_status with enum constraint
    op.add_column(
        'vendor_invoices',
        sa.Column(
            'payment_status',
            payment_status_enum,
            nullable=False,
            server_default='unpaid'
        )
    )
    
    # Ensure paid_amount exists (should already be there)
    if 'paid_amount' not in vendor_columns:
        op.add_column(
            'vendor_invoices',
            sa.Column('paid_amount', sa.Numeric(15, 2), server_default='0.00', nullable=False)
        )
    
    # Rename payment_date to paid_date if needed, or add paid_date
    if 'payment_date' in vendor_columns:
        op.alter_column('vendor_invoices', 'payment_date', new_column_name='paid_date')
    elif 'paid_date' not in vendor_columns:
        op.add_column(
            'vendor_invoices',
            sa.Column('paid_date', sa.Date, nullable=True)
        )
    
    # Add indexes for vendor_invoices
    op.create_index(
        'ix_vendor_invoices_payment_status',
        'vendor_invoices',
        ['payment_status'],
        unique=False
    )
    op.create_index(
        'ix_vendor_invoices_due_date_status',
        'vendor_invoices',
        ['due_date', 'payment_status'],
        unique=False
    )
    
    # === CUSTOMER INVOICES ===
    
    customer_columns = [col['name'] for col in inspector.get_columns('customer_invoices')]
    
    if 'payment_status' in customer_columns:
        # Drop the old column if it exists
        op.drop_column('customer_invoices', 'payment_status')
    
    # Add payment_status with enum constraint
    op.add_column(
        'customer_invoices',
        sa.Column(
            'payment_status',
            payment_status_enum,
            nullable=False,
            server_default='unpaid'
        )
    )
    
    # Ensure paid_amount exists
    if 'paid_amount' not in customer_columns:
        op.add_column(
            'customer_invoices',
            sa.Column('paid_amount', sa.Numeric(15, 2), server_default='0.00', nullable=False)
        )
    
    # Rename payment_date to paid_date if needed, or add paid_date
    if 'payment_date' in customer_columns:
        op.alter_column('customer_invoices', 'payment_date', new_column_name='paid_date')
    elif 'paid_date' not in customer_columns:
        op.add_column(
            'customer_invoices',
            sa.Column('paid_date', sa.Date, nullable=True)
        )
    
    # Add indexes for customer_invoices
    op.create_index(
        'ix_customer_invoices_payment_status',
        'customer_invoices',
        ['payment_status'],
        unique=False
    )
    op.create_index(
        'ix_customer_invoices_due_date_status',
        'customer_invoices',
        ['due_date', 'payment_status'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_vendor_invoices_payment_status', 'vendor_invoices')
    op.drop_index('ix_vendor_invoices_due_date_status', 'vendor_invoices')
    op.drop_index('ix_customer_invoices_payment_status', 'customer_invoices')
    op.drop_index('ix_customer_invoices_due_date_status', 'customer_invoices')
    
    # Revert columns to original state
    # Vendor invoices
    op.alter_column('vendor_invoices', 'paid_date', new_column_name='payment_date')
    op.drop_column('vendor_invoices', 'payment_status')
    op.add_column(
        'vendor_invoices',
        sa.Column('payment_status', sa.String(20), server_default='unpaid')
    )
    
    # Customer invoices
    op.alter_column('customer_invoices', 'paid_date', new_column_name='payment_date')
    op.drop_column('customer_invoices', 'payment_status')
    op.add_column(
        'customer_invoices',
        sa.Column('payment_status', sa.String(20), server_default='unpaid')
    )
    
    # Drop enum type
    payment_status_enum = ENUM(
        'unpaid', 'partially_paid', 'paid', 'overdue',
        name='payment_status_enum'
    )
    payment_status_enum.drop(op.get_bind(), checkfirst=True)
