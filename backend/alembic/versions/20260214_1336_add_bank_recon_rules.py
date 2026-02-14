"""add bank_reconciliation_rules to client_settings

Revision ID: 7f8e9d1c2b3a
Revises: bc1414beb0e0
Create Date: 2026-02-14 13:36:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7f8e9d1c2b3a'
down_revision = 'bc1414beb0e0'
branch_labels = None
depends_on = None


def upgrade():
    """Add bank_reconciliation_rules column to client_settings"""
    op.add_column(
        'client_settings',
        sa.Column(
            'bank_reconciliation_rules',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default='[]'
        )
    )


def downgrade():
    """Remove bank_reconciliation_rules column from client_settings"""
    op.drop_column('client_settings', 'bank_reconciliation_rules')
