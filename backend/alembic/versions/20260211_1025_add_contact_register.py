"""add_contact_register_tables

Revision ID: 20260211_1025_add_contact_register
Revises: 20260211_1016_add_opening_balance
Create Date: 2026-02-11 10:25:00

KONTAKTREGISTER - Supplier and Customer master data tables
Rules:
- No deletion allowed (only deactivation via status field)
- Unique org_number/birth_number per client
- Full audit trail for all changes
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '20260211_1025'
down_revision = '20260211_1016'
branch_labels = None
depends_on = None


def upgrade():
    """Create suppliers and customers contact register tables"""
    
    # 1. Create suppliers table (LEVERANDØRKORT)
    op.create_table(
        'suppliers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        
        # Basic information
        sa.Column('supplier_number', sa.String(50), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('org_number', sa.String(20), nullable=True),
        
        # Address
        sa.Column('address_line1', sa.String(255), nullable=True),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), server_default='Norge', nullable=False),
        
        # Contact
        sa.Column('contact_person', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        
        # Financial information
        sa.Column('bank_account', sa.String(50), nullable=True),
        sa.Column('iban', sa.String(50), nullable=True),
        sa.Column('swift_bic', sa.String(20), nullable=True),
        sa.Column('payment_terms_days', sa.Integer(), server_default='30', nullable=False),
        sa.Column('currency', sa.String(3), server_default='NOK', nullable=False),
        sa.Column('vat_code', sa.String(10), nullable=True),
        sa.Column('default_expense_account', sa.String(10), nullable=True),
        
        # System fields
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', UUID(as_uuid=True), nullable=True),
        
        # Constraints
        sa.CheckConstraint("status IN ('active', 'inactive')", name='ck_supplier_status'),
        sa.UniqueConstraint('client_id', 'supplier_number', name='uq_client_supplier_number'),
        sa.UniqueConstraint('client_id', 'org_number', name='uq_client_supplier_org_number'),
    )
    
    # Indexes for suppliers
    op.create_index('idx_suppliers_client', 'suppliers', ['client_id'])
    op.create_index('idx_suppliers_company_name', 'suppliers', ['company_name'])
    op.create_index('idx_suppliers_org_number', 'suppliers', ['org_number'])
    op.create_index('idx_suppliers_status', 'suppliers', ['status'])
    
    # 2. Create supplier_audit_logs table
    op.create_table(
        'supplier_audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('supplier_id', UUID(as_uuid=True), sa.ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('changed_fields', sa.Text(), nullable=True),
        sa.Column('old_values', sa.Text(), nullable=True),
        sa.Column('new_values', sa.Text(), nullable=True),
        sa.Column('performed_by', UUID(as_uuid=True), nullable=True),
        sa.Column('performed_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
    )
    
    # Indexes for supplier_audit_logs
    op.create_index('idx_supplier_audit_supplier', 'supplier_audit_logs', ['supplier_id'])
    op.create_index('idx_supplier_audit_performed_at', 'supplier_audit_logs', ['performed_at'])
    
    # 3. Create customers table (KUNDEKORT)
    op.create_table(
        'customers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        
        # Basic information
        sa.Column('customer_number', sa.String(50), nullable=False),
        sa.Column('is_company', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('org_number', sa.String(20), nullable=True),
        sa.Column('birth_number', sa.String(20), nullable=True),
        
        # Address
        sa.Column('address_line1', sa.String(255), nullable=True),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), server_default='Norge', nullable=False),
        
        # Contact
        sa.Column('contact_person', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        
        # Financial information
        sa.Column('payment_terms_days', sa.Integer(), server_default='14', nullable=False),
        sa.Column('currency', sa.String(3), server_default='NOK', nullable=False),
        sa.Column('vat_code', sa.String(10), nullable=True),
        sa.Column('default_revenue_account', sa.String(10), nullable=True),
        sa.Column('kid_prefix', sa.String(20), nullable=True),
        sa.Column('use_kid', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('credit_limit', sa.Integer(), nullable=True),
        sa.Column('reminder_fee', sa.Integer(), server_default='0', nullable=False),
        
        # System fields
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', UUID(as_uuid=True), nullable=True),
        
        # Constraints
        sa.CheckConstraint("status IN ('active', 'inactive')", name='ck_customer_status'),
        sa.UniqueConstraint('client_id', 'customer_number', name='uq_client_customer_number'),
        sa.UniqueConstraint('client_id', 'org_number', name='uq_client_customer_org_number'),
        sa.UniqueConstraint('client_id', 'birth_number', name='uq_client_customer_birth_number'),
    )
    
    # Indexes for customers
    op.create_index('idx_customers_client', 'customers', ['client_id'])
    op.create_index('idx_customers_name', 'customers', ['name'])
    op.create_index('idx_customers_org_number', 'customers', ['org_number'])
    op.create_index('idx_customers_birth_number', 'customers', ['birth_number'])
    op.create_index('idx_customers_status', 'customers', ['status'])
    
    # 4. Create customer_audit_logs table
    op.create_table(
        'customer_audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('changed_fields', sa.Text(), nullable=True),
        sa.Column('old_values', sa.Text(), nullable=True),
        sa.Column('new_values', sa.Text(), nullable=True),
        sa.Column('performed_by', UUID(as_uuid=True), nullable=True),
        sa.Column('performed_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
    )
    
    # Indexes for customer_audit_logs
    op.create_index('idx_customer_audit_customer', 'customer_audit_logs', ['customer_id'])
    op.create_index('idx_customer_audit_performed_at', 'customer_audit_logs', ['performed_at'])


def downgrade():
    """Remove contact register tables"""
    
    # Drop in reverse order (audit logs first, then main tables)
    op.drop_index('idx_customer_audit_performed_at', 'customer_audit_logs')
    op.drop_index('idx_customer_audit_customer', 'customer_audit_logs')
    op.drop_table('customer_audit_logs')
    
    op.drop_index('idx_customers_status', 'customers')
    op.drop_index('idx_customers_birth_number', 'customers')
    op.drop_index('idx_customers_org_number', 'customers')
    op.drop_index('idx_customers_name', 'customers')
    op.drop_index('idx_customers_client', 'customers')
    op.drop_table('customers')
    
    op.drop_index('idx_supplier_audit_performed_at', 'supplier_audit_logs')
    op.drop_index('idx_supplier_audit_supplier', 'supplier_audit_logs')
    op.drop_table('supplier_audit_logs')
    
    op.drop_index('idx_suppliers_status', 'suppliers')
    op.drop_index('idx_suppliers_org_number', 'suppliers')
    op.drop_index('idx_suppliers_company_name', 'suppliers')
    op.drop_index('idx_suppliers_client', 'suppliers')
    op.drop_table('suppliers')
