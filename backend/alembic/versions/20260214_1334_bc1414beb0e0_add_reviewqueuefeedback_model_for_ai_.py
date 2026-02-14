"""Add ReviewQueueFeedback model for AI learning

Revision ID: bc1414beb0e0
Revises: a21c38deec62
Create Date: 2026-02-14 13:34:59.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bc1414beb0e0'
down_revision: Union[str, None] = 'a21c38deec62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create review_queue_feedback table
    op.create_table('review_queue_feedback',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('review_queue_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('action', sa.String(length=20), nullable=False),
    sa.Column('ai_suggestion', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('accountant_correction', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('account_correct', sa.Boolean(), nullable=True),
    sa.Column('vat_correct', sa.Boolean(), nullable=True),
    sa.Column('fully_correct', sa.Boolean(), nullable=True),
    sa.Column('invoice_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['invoice_id'], ['vendor_invoices.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['review_queue_id'], ['review_queue.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_feedback_action_created', 'review_queue_feedback', ['action', 'created_at'], unique=False)
    op.create_index('idx_feedback_fully_correct', 'review_queue_feedback', ['fully_correct'], unique=False)
    op.create_index(op.f('ix_review_queue_feedback_action'), 'review_queue_feedback', ['action'], unique=False)
    op.create_index(op.f('ix_review_queue_feedback_created_at'), 'review_queue_feedback', ['created_at'], unique=False)
    op.create_index(op.f('ix_review_queue_feedback_invoice_id'), 'review_queue_feedback', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_review_queue_feedback_review_queue_id'), 'review_queue_feedback', ['review_queue_id'], unique=False)


def downgrade() -> None:
    # Drop review_queue_feedback table
    op.drop_index(op.f('ix_review_queue_feedback_review_queue_id'), table_name='review_queue_feedback')
    op.drop_index(op.f('ix_review_queue_feedback_invoice_id'), table_name='review_queue_feedback')
    op.drop_index(op.f('ix_review_queue_feedback_created_at'), table_name='review_queue_feedback')
    op.drop_index(op.f('ix_review_queue_feedback_action'), table_name='review_queue_feedback')
    op.drop_index('idx_feedback_fully_correct', table_name='review_queue_feedback')
    op.drop_index('idx_feedback_action_created', table_name='review_queue_feedback')
    op.drop_table('review_queue_feedback')
