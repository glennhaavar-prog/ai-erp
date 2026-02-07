"""add demo flags to tenants and clients

Revision ID: add_demo_flags_001
Revises: 2f33c4693fc8
Create Date: 2026-02-07 09:16:34.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_demo_flags_001'
down_revision: Union[str, None] = '2f33c4693fc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_demo column to tenants and clients tables"""
    
    # Add is_demo column to tenants
    op.add_column('tenants', sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add is_demo column to clients
    op.add_column('clients', sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create indexes for better query performance
    op.create_index('ix_tenants_is_demo', 'tenants', ['is_demo'])
    op.create_index('ix_clients_is_demo', 'clients', ['is_demo'])
    
    # Add demo_reset_at timestamp to track last reset
    op.add_column('tenants', sa.Column('demo_reset_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove demo flags"""
    
    # Drop columns and indexes
    op.drop_index('ix_clients_is_demo', table_name='clients')
    op.drop_index('ix_tenants_is_demo', table_name='tenants')
    op.drop_column('tenants', 'demo_reset_at')
    op.drop_column('clients', 'is_demo')
    op.drop_column('tenants', 'is_demo')
