"""Add type field to review_queue (simple)

Revision ID: 20260214_1625_simple
Revises: 20260214_1450
Create Date: 2026-02-14 16:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260214_1625_simple'
down_revision = '20260214_1450'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the enum type
    op.execute("""
        CREATE TYPE vouchertype AS ENUM (
            'SUPPLIER_INVOICE',
            'EMPLOYEE_EXPENSE',
            'INVENTORY_ADJUSTMENT',
            'MANUAL_CORRECTION',
            'OTHER'
        )
    """)
    
    # Add the type column with default value
    op.add_column(
        'review_queue',
        sa.Column(
            'type',
            sa.Enum(
                'SUPPLIER_INVOICE',
                'EMPLOYEE_EXPENSE',
                'INVENTORY_ADJUSTMENT',
                'MANUAL_CORRECTION',
                'OTHER',
                name='vouchertype'
            ),
            nullable=False,
            server_default='SUPPLIER_INVOICE'
        )
    )
    
    # Create index on the type column
    op.create_index(
        op.f('ix_review_queue_type'),
        'review_queue',
        ['type'],
        unique=False
    )


def downgrade() -> None:
    # Drop the index
    op.drop_index(op.f('ix_review_queue_type'), table_name='review_queue')
    
    # Drop the column
    op.drop_column('review_queue', 'type')
    
    # Drop the enum type
    op.execute('DROP TYPE vouchertype')
