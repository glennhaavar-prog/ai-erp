"""Initial database schema with all agent system tables

Revision ID: 001
Revises: 
Create Date: 2025-02-05 10:35:00.000000

Creates all 17 core tables for the AI-Agent ERP system:
- Multi-tenant architecture (tenants, clients, users)
- Agent system (agent_tasks, agent_events, agent_decisions, agent_learned_patterns)
- Accounting core (general_ledger, general_ledger_lines, chart_of_accounts)
- Vendor management (vendors, vendor_invoices)
- Review & learning (review_queue, corrections)
- Support (documents, audit_trail)

All tables include tenant_id for multi-tenancy (except tenants table).
Indexes optimized for query performance.
Constraints enforce data integrity.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables"""
    
    # ============================================================================
    # 1. TENANTS - Regnskapsbyrå (accounting firms)
    # ============================================================================
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('org_number', sa.String(20), nullable=False),
        sa.Column('subscription_tier', sa.String(20), nullable=False),
        sa.Column('max_clients', sa.Integer(), nullable=True),
        sa.Column('billing_email', sa.String(255), nullable=True),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_number', name='uq_tenants_org_number')
    )
    op.create_index('ix_tenants_name', 'tenants', ['name'])
    op.create_index('ix_tenants_org_number', 'tenants', ['org_number'])
    
    # ============================================================================
    # 2. CLIENTS - Customer companies under accounting firms
    # ============================================================================
    op.create_table(
        'clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_number', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('org_number', sa.String(20), nullable=False),
        sa.Column('ehf_endpoint', sa.String(255), nullable=True),
        sa.Column('active_banks', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('altinn_api_access', sa.Boolean(), nullable=True, default=False),
        sa.Column('fiscal_year_start', sa.Integer(), nullable=True, default=1),
        sa.Column('accounting_method', sa.String(20), nullable=True, default='accrual'),
        sa.Column('vat_term', sa.String(20), nullable=True, default='bimonthly'),
        sa.Column('base_currency', sa.String(3), nullable=True, default='NOK'),
        sa.Column('ai_automation_level', sa.String(20), nullable=False, default='assisted'),
        sa.Column('ai_confidence_threshold', sa.Integer(), nullable=True, default=85),
        sa.Column('status', sa.String(20), nullable=True, default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_number', name='uq_clients_org_number'),
        sa.UniqueConstraint('tenant_id', 'client_number', name='uq_tenant_client_number')
    )
    op.create_index('ix_clients_tenant_id', 'clients', ['tenant_id'])
    op.create_index('ix_clients_name', 'clients', ['name'])
    op.create_index('ix_clients_org_number', 'clients', ['org_number'])
    
    # ============================================================================
    # 3. USERS - Accountants/bookkeepers
    # ============================================================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('assigned_clients', postgresql.ARRAY(postgresql.UUID()), nullable=True),
        sa.Column('permissions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('national_id_hash', sa.String(255), nullable=True),
        sa.Column('bankid_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('last_bankid_verification', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email')
    )
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # ============================================================================
    # 4. CHART OF ACCOUNTS - Kontoplan (NS 4102)
    # ============================================================================
    op.create_table(
        'chart_of_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_number', sa.String(10), nullable=False),
        sa.Column('account_name', sa.String(255), nullable=False),
        sa.Column('account_type', sa.String(50), nullable=False),
        sa.Column('parent_account_number', sa.String(10), nullable=True),
        sa.Column('account_level', sa.Integer(), nullable=True, default=1),
        sa.Column('default_vat_code', sa.String(10), nullable=True),
        sa.Column('vat_deductible', sa.Boolean(), nullable=True, default=True),
        sa.Column('requires_reconciliation', sa.Boolean(), nullable=True, default=False),
        sa.Column('reconciliation_frequency', sa.String(20), nullable=True),
        sa.Column('ai_suggested_descriptions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('ai_usage_count', sa.Integer(), nullable=True, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id', 'account_number', name='uq_client_account_number')
    )
    op.create_index('ix_chart_of_accounts_client_id', 'chart_of_accounts', ['client_id'])
    op.create_index('ix_chart_of_accounts_account_number', 'chart_of_accounts', ['account_number'])
    
    # ============================================================================
    # 5. VENDORS - Leverandører
    # ============================================================================
    op.create_table(
        'vendors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_number', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('org_number', sa.String(20), nullable=True),
        sa.Column('contact_person', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('account_number', sa.String(10), nullable=False),
        sa.Column('payment_terms', sa.String(50), nullable=True, default='30'),
        sa.Column('default_vat_code', sa.String(10), nullable=True),
        sa.Column('bank_account', sa.String(50), nullable=True),
        sa.Column('iban', sa.String(50), nullable=True),
        sa.Column('swift_bic', sa.String(20), nullable=True),
        sa.Column('ai_learned_categories', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_average_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('ai_payment_pattern', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id', 'vendor_number', name='uq_client_vendor_number')
    )
    op.create_index('ix_vendors_client_id', 'vendors', ['client_id'])
    op.create_index('ix_vendors_name', 'vendors', ['name'])
    op.create_index('ix_vendors_org_number', 'vendors', ['org_number'])
    
    # ============================================================================
    # 6. DOCUMENTS - File storage metadata (S3)
    # ============================================================================
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('s3_bucket', sa.String(255), nullable=False),
        sa.Column('s3_key', sa.String(1024), nullable=False),
        sa.Column('s3_version_id', sa.String(255), nullable=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('ocr_text', sa.Text(), nullable=True),
        sa.Column('ocr_processed', sa.Boolean(), nullable=True, default=False),
        sa.Column('ocr_processed_at', sa.DateTime(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=False),
        sa.Column('download_url', sa.String(1024), nullable=True),
        sa.Column('download_url_expires_at', sa.DateTime(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('uploaded_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_client_id', 'documents', ['client_id'])
    op.create_index('ix_documents_s3_key', 'documents', ['s3_key'])
    op.create_index('ix_documents_file_hash', 'documents', ['file_hash'])
    
    # ============================================================================
    # 7. GENERAL LEDGER - Hovedbok (journal entries)
    # ============================================================================
    op.create_table(
        'general_ledger',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('accounting_date', sa.Date(), nullable=False),
        sa.Column('period', sa.String(7), nullable=False),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('voucher_number', sa.String(50), nullable=False),
        sa.Column('voucher_series', sa.String(10), nullable=True, default='A'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by_type', sa.String(20), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_reversed', sa.Boolean(), nullable=True, default=False),
        sa.Column('reversed_by_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reversal_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='posted'),
        sa.Column('locked', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['reversed_by_entry_id'], ['general_ledger.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id', 'voucher_series', 'voucher_number', name='uq_client_voucher')
    )
    op.create_index('ix_general_ledger_client_id', 'general_ledger', ['client_id'])
    op.create_index('ix_general_ledger_accounting_date', 'general_ledger', ['accounting_date'])
    op.create_index('ix_general_ledger_period', 'general_ledger', ['period'])
    op.create_index('ix_general_ledger_fiscal_year', 'general_ledger', ['fiscal_year'])
    op.create_index('ix_general_ledger_voucher_number', 'general_ledger', ['voucher_number'])
    
    # ============================================================================
    # 8. GENERAL LEDGER LINES - Journal entry lines (debit/credit)
    # ============================================================================
    op.create_table(
        'general_ledger_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('general_ledger_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('account_number', sa.String(10), nullable=False),
        sa.Column('debit_amount', sa.Numeric(15, 2), nullable=False, default=0.00),
        sa.Column('credit_amount', sa.Numeric(15, 2), nullable=False, default=0.00),
        sa.Column('vat_code', sa.String(10), nullable=True),
        sa.Column('vat_amount', sa.Numeric(15, 2), nullable=True, default=0.00),
        sa.Column('vat_base_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cost_center_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('line_description', sa.Text(), nullable=True),
        sa.Column('ai_confidence_score', sa.Integer(), nullable=True),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['general_ledger_id'], ['general_ledger.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('general_ledger_id', 'line_number', name='uq_gl_line_number'),
        sa.CheckConstraint('debit_amount >= 0 AND credit_amount >= 0', name='check_amounts_positive'),
        sa.CheckConstraint(
            '(debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0)',
            name='check_debit_or_credit'
        )
    )
    op.create_index('ix_general_ledger_lines_general_ledger_id', 'general_ledger_lines', ['general_ledger_id'])
    op.create_index('ix_general_ledger_lines_account_number', 'general_ledger_lines', ['account_number'])
    
    # ============================================================================
    # 9. VENDOR INVOICES - Leverandørfakturaer
    # ============================================================================
    op.create_table(
        'vendor_invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('invoice_number', sa.String(100), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('amount_excl_vat', sa.Numeric(15, 2), nullable=False),
        sa.Column('vat_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=True, default='NOK'),
        sa.Column('ehf_message_id', sa.String(255), nullable=True),
        sa.Column('ehf_raw_xml', sa.Text(), nullable=True),
        sa.Column('ehf_received_at', sa.DateTime(), nullable=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('general_ledger_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('booked_at', sa.DateTime(), nullable=True),
        sa.Column('payment_status', sa.String(20), nullable=False, default='unpaid'),
        sa.Column('paid_amount', sa.Numeric(15, 2), nullable=True, default=0.00),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('ai_processed', sa.Boolean(), nullable=True, default=False),
        sa.Column('ai_confidence_score', sa.Integer(), nullable=True),
        sa.Column('ai_booking_suggestion', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_detected_category', sa.String(100), nullable=True),
        sa.Column('ai_detected_issues', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        sa.Column('review_status', sa.String(20), nullable=False, default='pending'),
        sa.Column('reviewed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.ForeignKeyConstraint(['general_ledger_id'], ['general_ledger.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vendor_invoices_client_id', 'vendor_invoices', ['client_id'])
    op.create_index('ix_vendor_invoices_vendor_id', 'vendor_invoices', ['vendor_id'])
    op.create_index('ix_vendor_invoices_invoice_number', 'vendor_invoices', ['invoice_number'])
    op.create_index('ix_vendor_invoices_invoice_date', 'vendor_invoices', ['invoice_date'])
    op.create_index('ix_vendor_invoices_due_date', 'vendor_invoices', ['due_date'])
    op.create_index('ix_vendor_invoices_ehf_message_id', 'vendor_invoices', ['ehf_message_id'])
    
    # ============================================================================
    # 10. REVIEW QUEUE - Human review queue with priority routing
    # ============================================================================
    op.create_table(
        'review_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False, default='medium'),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('issue_category', sa.String(50), nullable=False),
        sa.Column('issue_description', sa.Text(), nullable=False),
        sa.Column('ai_suggestion', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_confidence', sa.Integer(), nullable=True),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        sa.Column('assigned_to_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('apply_to_similar', sa.Boolean(), nullable=True, default=False),
        sa.Column('similar_items_affected', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_review_queue_client_id', 'review_queue', ['client_id'])
    op.create_index('ix_review_queue_source_id', 'review_queue', ['source_id'])
    op.create_index('ix_review_queue_status', 'review_queue', ['status'])
    op.create_index('ix_review_queue_assigned_to_user_id', 'review_queue', ['assigned_to_user_id'])
    op.create_index('ix_review_queue_created_at', 'review_queue', ['created_at'])
    # Priority routing: status + priority composite index
    op.create_index('ix_review_queue_status_priority', 'review_queue', ['status', 'priority'])
    
    # ============================================================================
    # 11. AGENT TASKS - Task queue for specialist agents (WITH FOR UPDATE SKIP LOCKED)
    # ============================================================================
    op.create_table(
        'agent_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('task_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('priority', sa.Integer(), nullable=False, default=5),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('parent_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_task_id'], ['agent_tasks.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_tasks_tenant_id', 'agent_tasks', ['tenant_id'])
    op.create_index('ix_agent_tasks_agent_type', 'agent_tasks', ['agent_type'])
    op.create_index('ix_agent_tasks_status', 'agent_tasks', ['status'])
    op.create_index('ix_agent_tasks_created_at', 'agent_tasks', ['created_at'])
    # Critical index for task claiming with FOR UPDATE SKIP LOCKED
    op.create_index(
        'ix_agent_tasks_claim',
        'agent_tasks',
        ['agent_type', 'status', 'priority', 'created_at'],
        postgresql_where=sa.text("status = 'pending'")
    )
    
    # ============================================================================
    # 12. AGENT EVENTS - Event bus for orchestrator (with processed flag)
    # ============================================================================
    op.create_table(
        'agent_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_events_tenant_id', 'agent_events', ['tenant_id'])
    op.create_index('ix_agent_events_event_type', 'agent_events', ['event_type'])
    op.create_index('ix_agent_events_processed', 'agent_events', ['processed'])
    op.create_index('ix_agent_events_created_at', 'agent_events', ['created_at'])
    # Critical index for polling unprocessed events
    op.create_index(
        'ix_agent_events_unprocessed',
        'agent_events',
        ['processed', 'created_at'],
        postgresql_where=sa.text("processed = false")
    )
    
    # ============================================================================
    # 13. CORRECTIONS - Human corrections for learning (with batch support)
    # ============================================================================
    op.create_table(
        'corrections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('review_queue_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_entry', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('corrected_entry', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('correction_reason', sa.Text(), nullable=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('similar_corrected', sa.Integer(), nullable=True, default=0),
        sa.Column('corrected_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['review_queue_id'], ['review_queue.id']),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['general_ledger.id']),
        sa.ForeignKeyConstraint(['corrected_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_corrections_tenant_id', 'corrections', ['tenant_id'])
    op.create_index('ix_corrections_review_queue_id', 'corrections', ['review_queue_id'])
    op.create_index('ix_corrections_journal_entry_id', 'corrections', ['journal_entry_id'])
    op.create_index('ix_corrections_created_at', 'corrections', ['created_at'])
    # Batch support: index for finding corrections in same batch
    op.create_index('ix_corrections_batch_id', 'corrections', ['batch_id'])
    
    # ============================================================================
    # 14. AGENT LEARNED PATTERNS - Cross-client learning
    # ============================================================================
    op.create_table(
        'agent_learned_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pattern_type', sa.String(50), nullable=False),
        sa.Column('pattern_name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('action', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('applies_to_clients', postgresql.ARRAY(postgresql.UUID()), nullable=True),
        sa.Column('global_pattern', sa.Boolean(), nullable=True, default=False),
        sa.Column('success_rate', sa.Numeric(5, 4), nullable=True, default=0.0000),
        sa.Column('times_applied', sa.Integer(), nullable=True, default=0),
        sa.Column('times_correct', sa.Integer(), nullable=True, default=0),
        sa.Column('times_incorrect', sa.Integer(), nullable=True, default=0),
        sa.Column('confidence_boost', sa.Integer(), nullable=True, default=10),
        sa.Column('created_from_decision_ids', postgresql.ARRAY(postgresql.UUID()), nullable=True),
        sa.Column('learned_from_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_applied_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_learned_patterns_pattern_type', 'agent_learned_patterns', ['pattern_type'])
    op.create_index('ix_agent_learned_patterns_created_at', 'agent_learned_patterns', ['created_at'])
    op.create_index('ix_agent_learned_patterns_is_active', 'agent_learned_patterns', ['is_active'])
    
    # ============================================================================
    # 15. AGENT DECISIONS - AI decision logging
    # ============================================================================
    op.create_table(
        'agent_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('agent_session_id', sa.String(255), nullable=True),
        sa.Column('decision_type', sa.String(50), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('decision', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('confidence_score', sa.Integer(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('patterns_used', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('correct', sa.Boolean(), nullable=True),
        sa.Column('human_feedback', sa.Text(), nullable=True),
        sa.Column('corrected_decision', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('feedback_received_at', sa.DateTime(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_decisions_client_id', 'agent_decisions', ['client_id'])
    op.create_index('ix_agent_decisions_agent_type', 'agent_decisions', ['agent_type'])
    op.create_index('ix_agent_decisions_source_id', 'agent_decisions', ['source_id'])
    op.create_index('ix_agent_decisions_created_at', 'agent_decisions', ['created_at'])
    
    # ============================================================================
    # 16. AUDIT TRAIL - Immutable audit log (compliance)
    # ============================================================================
    op.create_table(
        'audit_trail',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('record_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('old_value', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('changed_by_type', sa.String(20), nullable=False),
        sa.Column('changed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('changed_by_name', sa.String(255), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_trail_client_id', 'audit_trail', ['client_id'])
    op.create_index('ix_audit_trail_table_name', 'audit_trail', ['table_name'])
    op.create_index('ix_audit_trail_record_id', 'audit_trail', ['record_id'])
    op.create_index('ix_audit_trail_timestamp', 'audit_trail', ['timestamp'])
    

def downgrade() -> None:
    """Drop all tables in reverse order"""
    op.drop_table('audit_trail')
    op.drop_table('agent_decisions')
    op.drop_table('agent_learned_patterns')
    op.drop_table('corrections')
    op.drop_table('agent_events')
    op.drop_table('agent_tasks')
    op.drop_table('review_queue')
    op.drop_table('vendor_invoices')
    op.drop_table('general_ledger_lines')
    op.drop_table('general_ledger')
    op.drop_table('documents')
    op.drop_table('vendors')
    op.drop_table('chart_of_accounts')
    op.drop_table('users')
    op.drop_table('clients')
    op.drop_table('tenants')
