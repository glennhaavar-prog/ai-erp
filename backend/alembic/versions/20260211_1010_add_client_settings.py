"""add_client_settings_table

Revision ID: 20260211_1010_add_client_settings
Revises: 20260210_0900_dnb_bank_connections_clean
Create Date: 2026-02-11 10:10:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20260211_1010'
down_revision = '20260210_0900'
branch_labels = None
depends_on = None


def upgrade():
    """Create client_settings table for FIRMAINNSTILLINGER"""
    
    op.create_table(
        'client_settings',
        # Primary Key
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # Foreign Key to Client (one-to-one)
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, unique=True),
        
        # ===== SECTION 1: COMPANY INFO =====
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('org_number', sa.String(20), nullable=False),
        sa.Column('address_street', sa.String(255), nullable=True),
        sa.Column('address_postal_code', sa.String(10), nullable=True),
        sa.Column('address_city', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('ceo_name', sa.String(255), nullable=True),
        sa.Column('chairman_name', sa.String(255), nullable=True),
        sa.Column('industry', sa.String(255), nullable=True),
        sa.Column('nace_code', sa.String(10), nullable=True),
        sa.Column('accounting_year_start_month', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('incorporation_date', sa.Date(), nullable=True),
        sa.Column('legal_form', sa.String(20), nullable=False, server_default='AS'),
        
        # ===== SECTION 2: ACCOUNTING SETTINGS =====
        sa.Column('chart_of_accounts', sa.String(50), nullable=False, server_default='NS4102'),
        sa.Column('vat_registered', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('vat_period', sa.String(20), nullable=False, server_default='bimonthly'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='NOK'),
        sa.Column('rounding_rules', JSON, nullable=True),
        
        # ===== SECTION 3: BANK ACCOUNTS =====
        sa.Column('bank_accounts', JSON, nullable=False, server_default='[]'),
        
        # ===== SECTION 4: PAYROLL/EMPLOYEES =====
        sa.Column('has_employees', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('payroll_frequency', sa.String(20), nullable=True),
        sa.Column('employer_tax_zone', sa.String(20), nullable=True),
        
        # ===== SECTION 5: SERVICES =====
        sa.Column('services_provided', JSON, nullable=False, server_default='{}'),
        sa.Column('task_templates', JSON, nullable=False, server_default='[]'),
        
        # ===== SECTION 6: RESPONSIBLE ACCOUNTANT =====
        sa.Column('responsible_accountant_name', sa.String(255), nullable=True),
        sa.Column('responsible_accountant_email', sa.String(255), nullable=True),
        sa.Column('responsible_accountant_phone', sa.String(20), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes
    op.create_index('idx_client_settings_client_id', 'client_settings', ['client_id'])
    
    # Create default settings for existing clients
    op.execute("""
        INSERT INTO client_settings (
            client_id,
            company_name,
            org_number,
            accounting_year_start_month,
            legal_form,
            chart_of_accounts,
            vat_registered,
            vat_period,
            currency,
            rounding_rules,
            bank_accounts,
            has_employees,
            services_provided,
            task_templates
        )
        SELECT
            id as client_id,
            name as company_name,
            org_number,
            COALESCE(fiscal_year_start, 1) as accounting_year_start_month,
            'AS' as legal_form,
            'NS4102' as chart_of_accounts,
            true as vat_registered,
            COALESCE(vat_term, 'bimonthly') as vat_period,
            COALESCE(base_currency, 'NOK') as currency,
            '{"decimals": 2, "method": "standard"}'::json as rounding_rules,
            '[]'::json as bank_accounts,
            false as has_employees,
            '{"bookkeeping": true, "payroll": false, "annual_accounts": true, "vat_reporting": true, "other": []}'::json as services_provided,
            '[]'::json as task_templates
        FROM clients
        WHERE NOT EXISTS (
            SELECT 1 FROM client_settings WHERE client_settings.client_id = clients.id
        )
    """)


def downgrade():
    """Drop client_settings table"""
    op.drop_index('idx_client_settings_client_id', 'client_settings')
    op.drop_table('client_settings')
