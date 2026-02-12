"""add_ai_features_fields

Add fields for AI features: payment_terms_days and contextual_help_texts table

Revision ID: add_ai_features
Revises: (latest)
Create Date: 2026-02-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_ai_features'
down_revision = '20260211_1310'  # Currency rates migration
branch_labels = None
depends_on = None


def upgrade():
    # Add payment_terms_days to vendor_invoices
    op.add_column('vendor_invoices',
        sa.Column('payment_terms_days', sa.Integer(), nullable=True)
    )
    
    # Create contextual_help_texts table
    op.create_table('contextual_help_texts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page', sa.String(length=100), nullable=False),
        sa.Column('field', sa.String(length=100), nullable=False),
        sa.Column('user_role', sa.String(length=50), nullable=False),
        sa.Column('help_text', sa.Text(), nullable=False),
        sa.Column('detailed_help', sa.Text(), nullable=True),
        sa.Column('example_text', sa.String(length=255), nullable=True),
        sa.Column('language', sa.String(length=5), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for contextual_help_texts
    op.create_index('ix_contextual_help_page', 'contextual_help_texts', ['page'])
    op.create_index('ix_contextual_help_field', 'contextual_help_texts', ['field'])
    op.create_index('ix_contextual_help_role', 'contextual_help_texts', ['user_role'])
    
    # Create unique constraint for lookup
    op.create_index(
        'ix_contextual_help_lookup',
        'contextual_help_texts',
        ['page', 'field', 'user_role', 'language'],
        unique=True
    )


def downgrade():
    # Drop contextual_help_texts table
    op.drop_index('ix_contextual_help_lookup', table_name='contextual_help_texts')
    op.drop_index('ix_contextual_help_role', table_name='contextual_help_texts')
    op.drop_index('ix_contextual_help_field', table_name='contextual_help_texts')
    op.drop_index('ix_contextual_help_page', table_name='contextual_help_texts')
    op.drop_table('contextual_help_texts')
    
    # Remove payment_terms_days from vendor_invoices
    op.drop_column('vendor_invoices', 'payment_terms_days')
