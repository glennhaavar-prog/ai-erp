"""Add VoucherAuditLog model (clean)

Revision ID: 20260214_1704
Revises: 20260214_1630_nullable
Create Date: 2026-02-14 17:04:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260214_1704'
down_revision = '20260214_1630_nullable'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create VoucherAuditLog table
    op.create_table('voucher_audit_log',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('voucher_id', sa.UUID(), nullable=False),
        sa.Column('voucher_type', sa.Enum('SUPPLIER_INVOICE', 'OTHER_VOUCHER', 'BANK_RECON', 'BALANCE_RECON', name='auditvouchertype'), nullable=False),
        sa.Column('action', sa.Enum('CREATED', 'AI_SUGGESTED', 'APPROVED', 'REJECTED', 'CORRECTED', 'RULE_APPLIED', name='auditaction'), nullable=False),
        sa.Column('performed_by', sa.Enum('AI', 'ACCOUNTANT', 'SUPERVISOR', 'MANAGER', name='performedby'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_voucher_audit_log_action'), 'voucher_audit_log', ['action'], unique=False)
    op.create_index('ix_voucher_audit_log_action_time', 'voucher_audit_log', ['action', 'timestamp'], unique=False)
    op.create_index(op.f('ix_voucher_audit_log_performed_by'), 'voucher_audit_log', ['performed_by'], unique=False)
    op.create_index('ix_voucher_audit_log_timeline', 'voucher_audit_log', ['voucher_id', 'timestamp'], unique=False)
    op.create_index(op.f('ix_voucher_audit_log_timestamp'), 'voucher_audit_log', ['timestamp'], unique=False)
    op.create_index(op.f('ix_voucher_audit_log_user_id'), 'voucher_audit_log', ['user_id'], unique=False)
    op.create_index(op.f('ix_voucher_audit_log_voucher_id'), 'voucher_audit_log', ['voucher_id'], unique=False)
    op.create_index('ix_voucher_audit_log_voucher_lookup', 'voucher_audit_log', ['voucher_id', 'voucher_type'], unique=False)
    op.create_index(op.f('ix_voucher_audit_log_voucher_type'), 'voucher_audit_log', ['voucher_type'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_voucher_audit_log_voucher_type'), table_name='voucher_audit_log')
    op.drop_index('ix_voucher_audit_log_voucher_lookup', table_name='voucher_audit_log')
    op.drop_index(op.f('ix_voucher_audit_log_voucher_id'), table_name='voucher_audit_log')
    op.drop_index(op.f('ix_voucher_audit_log_user_id'), table_name='voucher_audit_log')
    op.drop_index(op.f('ix_voucher_audit_log_timestamp'), table_name='voucher_audit_log')
    op.drop_index('ix_voucher_audit_log_timeline', table_name='voucher_audit_log')
    op.drop_index(op.f('ix_voucher_audit_log_performed_by'), table_name='voucher_audit_log')
    op.drop_index('ix_voucher_audit_log_action_time', table_name='voucher_audit_log')
    op.drop_index(op.f('ix_voucher_audit_log_action'), table_name='voucher_audit_log')
    
    # Drop table
    op.drop_table('voucher_audit_log')
    
    # Drop enums
    sa.Enum(name='auditvouchertype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='auditaction').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='performedby').drop(op.get_bind(), checkfirst=True)
