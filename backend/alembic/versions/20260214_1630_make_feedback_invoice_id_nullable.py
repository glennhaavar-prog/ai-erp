"""Make invoice_id nullable in review_queue_feedback

Revision ID: 20260214_1630_nullable
Revises: 20260214_1625_simple
Create Date: 2026-02-14 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260214_1630_nullable'
down_revision = '20260214_1625_simple'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Make invoice_id nullable to support feedback for other voucher types
    (employee expenses, inventory adjustments, etc.)
    """
    # Make invoice_id nullable
    op.alter_column(
        'review_queue_feedback',
        'invoice_id',
        existing_type=sa.UUID(),
        nullable=True
    )


def downgrade() -> None:
    """Revert invoice_id to NOT NULL"""
    # Make invoice_id NOT NULL again
    op.alter_column(
        'review_queue_feedback',
        'invoice_id',
        existing_type=sa.UUID(),
        nullable=False
    )
