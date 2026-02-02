# AI-Agent ERP System - Database Skisse
**Versjon:** 1.0  
**Dato:** 2026-02-02  
**Cloud Platform:** AWS (RDS PostgreSQL)  
**Arkitektur:** Multi-tenant

---

## 🎯 System Oversikt

### Tre Separate Interfaces:
1. **Agent Workspace** - Kun for AI-agent (admin kan overstyre)
2. **Accountant Dashboard** - Multi-tenant, håndterer flere klienter samtidig
3. **Customer Portal** - For sluttkunder

### Agent Strategi:
- **Én hovedagent** med oversikt over alle moduler
- Cross-module forståelse (bokføring ↔ avstemming ↔ bank)
- **Cross-client læring** - agenten lærer fra alle klienter i systemet
- **Confidence-based routing** - usikre case → human review queue

---

## 📊 CORE TABLES

### 1. Multi-Tenant Struktur

```sql
-- Regnskapsbyrå (accounting firms)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    org_number VARCHAR(20) UNIQUE NOT NULL,
    subscription_tier VARCHAR(50), -- basic/professional/enterprise
    max_clients INTEGER,
    billing_email VARCHAR(255),
    settings JSONB, -- tenant-specific config
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Klienter under hvert byrå
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    client_number VARCHAR(50) NOT NULL, -- Sequential per tenant
    name VARCHAR(255) NOT NULL,
    org_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Integrations
    ehf_endpoint VARCHAR(255), -- Pepol access point
    active_banks JSONB, -- Array of connected banks
    altinn_api_access BOOLEAN DEFAULT false,
    
    -- Fiscal setup
    fiscal_year_start INTEGER DEFAULT 1, -- Month (1=Jan)
    accounting_method VARCHAR(20) DEFAULT 'accrual', -- accrual/cash
    vat_term VARCHAR(20) DEFAULT 'bimonthly', -- monthly/bimonthly/annual
    
    -- Agent settings
    ai_automation_level VARCHAR(20) DEFAULT 'assisted', -- full/assisted/manual
    ai_confidence_threshold INTEGER DEFAULT 85, -- Min confidence for auto-booking
    
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(tenant_id, client_number)
);

-- Brukere (accountants)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- admin/senior_accountant/accountant/viewer
    
    -- Access control
    assigned_clients UUID[], -- Array of client IDs this user can access
    permissions JSONB, -- Granular permissions
    
    -- BankID
    national_id_hash VARCHAR(255), -- Hashed fødselsnummer for audit
    bankid_verified BOOLEAN DEFAULT false,
    last_bankid_verification TIMESTAMP,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

**💡 MITT FORSLAG:** Jeg la til:
- `subscription_tier` - ulike prispakker for regnskapsbyrå
- `client_number` - sekvensiell nummerering per tenant (lettere å referere til)
- `ai_automation_level` - la klienter velge hvor mye AI skal gjøre automatisk
- `ai_confidence_threshold` - justerbar terskel per klient
- `permissions JSONB` - granulær tilgangskontroll

---

## 📚 GENERAL LEDGER & CHART OF ACCOUNTS

```sql
-- Kontoplan
CREATE TABLE chart_of_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    account_number VARCHAR(10) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL, -- asset/liability/equity/revenue/expense
    
    -- Hierarchy
    parent_account_number VARCHAR(10), -- For sub-accounts
    account_level INTEGER DEFAULT 1,
    
    -- VAT & Tax
    default_vat_code VARCHAR(10),
    vat_deductible BOOLEAN DEFAULT true,
    
    -- Reconciliation
    requires_reconciliation BOOLEAN DEFAULT false,
    reconciliation_frequency VARCHAR(20), -- daily/monthly/quarterly
    
    -- Agent learning
    ai_suggested_description TEXT[], -- Descriptions agent learned for this account
    ai_usage_count INTEGER DEFAULT 0, -- How often agent uses this account
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(client_id, account_number)
);

-- Hovedbok (immutable journal entries)
CREATE TABLE general_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE RESTRICT,
    
    -- Dates
    entry_date DATE NOT NULL, -- When entry was created
    accounting_date DATE NOT NULL, -- Accounting period date
    period VARCHAR(7) NOT NULL, -- YYYY-MM format
    fiscal_year INTEGER NOT NULL,
    
    -- Voucher
    voucher_number VARCHAR(50) NOT NULL, -- Bilagsnummer
    voucher_series VARCHAR(10) DEFAULT 'A', -- A/B/C series
    description TEXT NOT NULL,
    
    -- Source tracking
    source_type VARCHAR(50) NOT NULL, -- ehf_invoice/bank_transaction/manual/correction/opening_balance
    source_id UUID, -- FK to source table (vendor_invoices, bank_transactions, etc)
    
    -- Creator tracking
    created_by_type VARCHAR(20) NOT NULL, -- ai_agent/user
    created_by_id UUID, -- user_id if human, agent_session_id if AI
    
    -- Reversal handling
    is_reversed BOOLEAN DEFAULT false,
    reversed_by_entry_id UUID REFERENCES general_ledger(id),
    reversal_reason TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'posted', -- draft/posted/reversed
    locked BOOLEAN DEFAULT false, -- Can't be changed after period close
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(client_id, voucher_series, voucher_number)
);

-- Bilagslinjer (debit/credit lines)
CREATE TABLE general_ledger_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    general_ledger_id UUID REFERENCES general_ledger(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL, -- Sequence within voucher
    
    -- Accounting
    account_number VARCHAR(10) NOT NULL,
    debit_amount DECIMAL(15,2) DEFAULT 0.00,
    credit_amount DECIMAL(15,2) DEFAULT 0.00,
    
    -- VAT
    vat_code VARCHAR(10),
    vat_amount DECIMAL(15,2) DEFAULT 0.00,
    vat_base_amount DECIMAL(15,2), -- Amount VAT is calculated from
    
    -- Dimensions (optional)
    department_id UUID,
    project_id UUID,
    cost_center_id UUID,
    
    -- Description
    line_description TEXT,
    
    -- Agent metadata
    ai_confidence_score INTEGER, -- 0-100 for this specific line
    ai_reasoning TEXT, -- Why agent chose this account
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(general_ledger_id, line_number)
);

-- CHECK: Debit = Credit per entry
ALTER TABLE general_ledger ADD CONSTRAINT check_balanced
    CHECK ((SELECT SUM(debit_amount) - SUM(credit_amount) 
            FROM general_ledger_lines 
            WHERE general_ledger_id = id) = 0);
```

**💡 MITT FORSLAG:**
- `voucher_series` - A/B/C serier for ulike bilagstyper (standard i Norge)
- `period` og `fiscal_year` - enklere rapportering
- `locked` - hindrer endringer etter periodeavslutning
- `ai_reasoning` - viktig for å forstå agentens beslutninger
- **CHECK constraint** - sikrer at debit alltid = credit
- `ai_suggested_description` i chart_of_accounts - agenten lærer vanlige beskrivelser

---

## 👥 SUB-LEDGERS (Reskontro)

```sql
-- Leverandører
CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    vendor_number VARCHAR(50) NOT NULL,
    
    -- Company info
    name VARCHAR(255) NOT NULL,
    org_number VARCHAR(20),
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    
    -- Accounting
    account_number VARCHAR(10) NOT NULL, -- FK to chart_of_accounts
    payment_terms VARCHAR(50), -- "30 days net"
    default_vat_code VARCHAR(10),
    
    -- Banking
    bank_account VARCHAR(50),
    iban VARCHAR(50),
    swift_bic VARCHAR(20),
    
    -- Agent learning
    ai_learned_categories JSONB, -- Common expense categories for this vendor
    ai_average_amount DECIMAL(15,2), -- Helps detect anomalies
    ai_payment_pattern VARCHAR(50), -- "always on time" / "usually late"
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(client_id, vendor_number)
);

-- Leverandørfakturaer (EHF innkommende)
CREATE TABLE vendor_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE RESTRICT,
    vendor_id UUID REFERENCES vendors(id),
    
    -- Invoice details
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    
    -- Amounts
    amount_excl_vat DECIMAL(15,2) NOT NULL,
    vat_amount DECIMAL(15,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    
    -- EHF data
    ehf_message_id VARCHAR(255), -- Original EHF message ID
    ehf_raw_xml TEXT, -- Store complete EHF for audit
    ehf_received_at TIMESTAMP,
    
    -- Document storage
    document_id UUID, -- FK to documents table (PDF)
    
    -- Booking
    general_ledger_id UUID REFERENCES general_ledger(id),
    booked_at TIMESTAMP,
    
    -- Payment tracking
    payment_status VARCHAR(20) DEFAULT 'unpaid', -- unpaid/partial/paid/overdue
    paid_amount DECIMAL(15,2) DEFAULT 0.00,
    payment_date DATE,
    
    -- AI processing
    ai_processed BOOLEAN DEFAULT false,
    ai_confidence_score INTEGER, -- 0-100
    ai_booking_suggestion JSONB, -- What agent suggests
    ai_detected_category VARCHAR(100),
    ai_detected_issues JSONB, -- Array of potential problems
    
    -- Review queue
    review_status VARCHAR(20) DEFAULT 'pending', -- pending/auto_approved/needs_review/reviewed/rejected
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(client_id, vendor_id, invoice_number)
);

-- Kunder
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    customer_number VARCHAR(50) NOT NULL,
    
    -- Company info
    name VARCHAR(255) NOT NULL,
    org_number VARCHAR(20),
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    
    -- Address
    address JSONB, -- {street, city, postal_code, country}
    
    -- Accounting
    account_number VARCHAR(10) NOT NULL,
    payment_terms VARCHAR(50),
    default_vat_code VARCHAR(10),
    credit_limit DECIMAL(15,2),
    
    -- Agent insights
    ai_payment_reliability INTEGER, -- Score 0-100
    ai_average_days_to_pay INTEGER,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(client_id, customer_number)
);

-- Kundefakturaer (utgående)
CREATE TABLE customer_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE RESTRICT,
    customer_id UUID REFERENCES customers(id),
    
    -- Invoice details
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    
    -- Amounts
    amount_excl_vat DECIMAL(15,2) NOT NULL,
    vat_amount DECIMAL(15,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    
    -- Payment reference
    kid_number VARCHAR(50), -- KID/OCR number for payment matching
    
    -- Document
    document_id UUID,
    
    -- Booking
    general_ledger_id UUID REFERENCES general_ledger(id),
    booked_at TIMESTAMP,
    
    -- Payment tracking
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    paid_amount DECIMAL(15,2) DEFAULT 0.00,
    payment_date DATE,
    
    -- EHF sending (if applicable)
    ehf_sent BOOLEAN DEFAULT false,
    ehf_sent_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(client_id, invoice_number)
);
```

**💡 MITT FORSLAG:**
- `ai_learned_categories` - agenten lærer hvilke kontoer som er vanlige for hver leverandør
- `ai_average_amount` - brukes til å oppdage uvanlige beløp
- `ai_payment_pattern` - lærer betalingsmønster
- `ai_detected_issues` - array av potensielle problemer agenten finner
- `review_notes` - regnskapsfører kan legge til notater
- `credit_limit` for kunder - agenten kan varsle ved overlimit

---

## 🏦 BANKING MODULE

```sql
-- Bankkontoer
CREATE TABLE bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Account details
    account_number VARCHAR(10) NOT NULL, -- FK to chart_of_accounts
    bank_name VARCHAR(100) NOT NULL,
    iban VARCHAR(50),
    account_number_bank VARCHAR(50), -- Actual bank account number
    
    -- API Integration
    bank_api_provider VARCHAR(50), -- DNB/SpareBank1/Nordea/etc
    api_credentials_encrypted TEXT, -- Encrypted API keys
    api_last_sync TIMESTAMP,
    api_sync_enabled BOOLEAN DEFAULT true,
    
    -- Balance tracking
    current_balance DECIMAL(15,2),
    last_balance_update TIMESTAMP,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(client_id, account_number)
);

-- Banktransaksjoner
CREATE TABLE bank_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_account_id UUID REFERENCES bank_accounts(id) ON DELETE RESTRICT,
    
    -- Transaction details
    transaction_date DATE NOT NULL,
    value_date DATE, -- When funds are available
    amount DECIMAL(15,2) NOT NULL,
    transaction_type VARCHAR(20), -- debit/credit
    
    -- Description
    description TEXT NOT NULL,
    bank_reference VARCHAR(100),
    
    -- Payment references
    kid_number VARCHAR(50), -- KID/OCR if present
    counterparty_account VARCHAR(50),
    counterparty_name VARCHAR(255),
    
    -- Booking
    general_ledger_id UUID REFERENCES general_ledger(id),
    booked_at TIMESTAMP,
    
    -- Matching
    matched_invoice_id UUID, -- vendor_invoice or customer_invoice
    matched_invoice_type VARCHAR(20), -- vendor/customer
    match_confidence INTEGER, -- 0-100
    match_method VARCHAR(50), -- kid_match/amount_match/ai_match/manual
    
    -- AI processing
    ai_suggested_account VARCHAR(10),
    ai_suggested_match_id UUID,
    ai_confidence_score INTEGER,
    ai_reasoning TEXT,
    
    -- Review
    review_status VARCHAR(20) DEFAULT 'pending',
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    
    -- Import metadata
    imported_at TIMESTAMP DEFAULT NOW(),
    import_batch_id UUID, -- Group transactions from same import
    
    UNIQUE(bank_account_id, transaction_date, amount, bank_reference)
);

-- Betalingskø
CREATE TABLE payment_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    vendor_invoice_id UUID REFERENCES vendor_invoices(id),
    bank_account_id UUID REFERENCES bank_accounts(id),
    
    -- Payment details
    amount DECIMAL(15,2) NOT NULL,
    due_date DATE NOT NULL,
    payment_date DATE, -- Scheduled payment date
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending/approved/scheduled/sent/completed/failed
    
    -- BankID workflow
    requires_bankid BOOLEAN DEFAULT true,
    bankid_requested_at TIMESTAMP,
    bankid_completed_by UUID REFERENCES users(id),
    bankid_completed_at TIMESTAMP,
    
    -- API response
    bank_api_reference VARCHAR(255), -- Reference from bank API
    bank_response JSONB,
    error_message TEXT,
    
    -- Agent metadata
    ai_suggested_date DATE, -- When agent thinks we should pay
    ai_priority VARCHAR(20), -- urgent/normal/low
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**💡 MITT FORSLAG:**
- `import_batch_id` - grupper transaksjoner fra samme import
- `match_method` - spor hvordan matching skjedde
- `ai_suggested_date` i payment_queue - agenten foreslår optimal betalingstidspunkt
- `ai_priority` - agenten prioriterer betalinger basert på vilkår, rabatter osv
- `bank_response JSONB` - lagre fullstendig respons fra bank API for debugging

---

## 🔄 RECONCILIATION MODULE

```sql
-- Avstemmingsoppgaver
CREATE TABLE reconciliation_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Task details
    task_name VARCHAR(255) NOT NULL,
    reconciliation_type VARCHAR(50) NOT NULL, -- bank/vendor/customer/vat/inventory/fixed_assets
    
    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Accounts involved
    account_numbers VARCHAR(10)[], -- Array of accounts to reconcile
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending/in_progress/completed/failed/requires_review
    
    -- Execution
    assigned_to_agent BOOLEAN DEFAULT true,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results summary
    total_items_checked INTEGER,
    matched_items INTEGER,
    unmatched_items INTEGER,
    discrepancy_count INTEGER,
    total_discrepancy_amount DECIMAL(15,2),
    
    -- Review
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Avstemmingsresultater
CREATE TABLE reconciliation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES reconciliation_tasks(id) ON DELETE CASCADE,
    
    -- Datasets compared
    dataset_a_source VARCHAR(50), -- e.g., "bank_statement"
    dataset_a JSONB, -- Actual data compared
    
    dataset_b_source VARCHAR(50), -- e.g., "general_ledger"
    dataset_b JSONB,
    
    -- Matching results
    matched_items JSONB, -- Array of {a_id, b_id, amount}
    unmatched_a JSONB, -- Items in A not in B
    unmatched_b JSONB, -- Items in B not in A
    
    -- Discrepancies
    discrepancies JSONB, -- Array of {type, a_id, b_id, difference, explanation}
    
    -- Status
    status VARCHAR(20), -- ok/minor_discrepancy/major_discrepancy
    requires_action BOOLEAN DEFAULT false,
    
    -- AI analysis
    ai_confidence INTEGER,
    ai_suggested_resolution JSONB,
    ai_risk_level VARCHAR(20), -- low/medium/high
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Avstemmingshandlinger (corrections made during reconciliation)
CREATE TABLE reconciliation_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reconciliation_result_id UUID REFERENCES reconciliation_results(id),
    
    action_type VARCHAR(50), -- create_entry/adjust_entry/flag_for_review
    description TEXT NOT NULL,
    
    -- If creating/adjusting GL entry
    general_ledger_id UUID REFERENCES general_ledger(id),
    
    -- Approval
    suggested_by_type VARCHAR(20), -- ai_agent/user
    suggested_by_id UUID,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    
    status VARCHAR(20) DEFAULT 'pending', -- pending/approved/rejected
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

**💡 MITT FORSLAG:**
- `reconciliation_type` inkluderer flere typer - også inventory og fixed assets for fremtiden
- `ai_risk_level` - agenten vurderer risiko ved avvik
- `reconciliation_actions` tabell - sporer korrigeringer foreslått under avstemming
- `account_numbers` array - kan avstemme flere kontoer samtidig

---

## 📋 AUDIT TRAIL & LEARNING

```sql
-- Fullstendig revisjonslogg (immutable)
CREATE TABLE audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    
    -- What was changed
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL, -- create/update/delete/reverse
    
    -- Changes
    old_value JSONB, -- Full record before change
    new_value JSONB, -- Full record after change
    changed_fields TEXT[], -- Array of field names that changed
    
    -- Who changed it
    changed_by_type VARCHAR(20) NOT NULL, -- ai_agent/user/system
    changed_by_id UUID, -- user_id or agent_session_id
    changed_by_name VARCHAR(255), -- For easy reading
    
    -- Why changed
    reason TEXT,
    triggered_by VARCHAR(50), -- manual/automatic/scheduled/correction
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_client_table ON audit_trail(client_id, table_name);
CREATE INDEX idx_audit_record ON audit_trail(table_name, record_id);
CREATE INDEX idx_audit_timestamp ON audit_trail(timestamp);

-- Agent-beslutninger (læring)
CREATE TABLE agent_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    
    -- Decision context
    decision_type VARCHAR(50) NOT NULL, -- booking/matching/reconciliation/categorization
    context JSONB NOT NULL, -- What the agent saw (invoice, transaction, etc)
    
    -- Decision made
    decision JSONB NOT NULL, -- What agent decided
    confidence_score INTEGER NOT NULL, -- 0-100
    reasoning TEXT, -- Agent's explanation
    alternative_options JSONB, -- Other options agent considered
    
    -- Learning from feedback
    human_override BOOLEAN DEFAULT false,
    human_feedback TEXT,
    correct BOOLEAN, -- Was the decision correct?
    feedback_given_by UUID REFERENCES users(id),
    feedback_given_at TIMESTAMP,
    
    -- Impact
    general_ledger_id UUID REFERENCES general_ledger(id),
    
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agent_decisions_type ON agent_decisions(decision_type, correct);
CREATE INDEX idx_agent_decisions_client ON agent_decisions(client_id, timestamp);

-- Agent læring på tvers av klienter
CREATE TABLE agent_learned_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    pattern_type VARCHAR(50) NOT NULL, -- vendor_category/account_selection/amount_anomaly
    pattern_description TEXT NOT NULL,
    
    -- Pattern data
    pattern_trigger JSONB, -- What triggers this pattern
    pattern_action JSONB, -- What to do when pattern is detected
    
    -- Evidence
    based_on_decisions UUID[], -- Array of agent_decision IDs
    success_rate DECIMAL(5,2), -- Percentage (0-100)
    times_applied INTEGER DEFAULT 0,
    
    -- Scope
    applies_to_clients UUID[], -- Specific clients, or NULL for all
    applies_to_industries VARCHAR(50)[], -- Can be industry-specific
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP
);
```

**💡 MITT FORSLAG:**
- `changed_fields` array - lett å se hva som faktisk endret seg
- `alternative_options` - se hva agenten vurderte men valgte bort
- `agent_learned_patterns` - VIKTIG tabell for cross-client læring!
- `success_rate` - spor hvor godt mønsteret fungerer
- `applies_to_industries` - noen patterns er bransje-spesifikke

---

## 🤖 HUMAN REVIEW & FEEDBACK

```sql
-- Oppgaver som trenger menneskelig review
CREATE TABLE review_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Priority
    priority VARCHAR(20) DEFAULT 'normal', -- low/normal/high/critical
    due_date TIMESTAMP, -- When this should be resolved by
    
    -- What needs review
    item_type VARCHAR(50) NOT NULL, -- vendor_invoice/bank_transaction/reconciliation/correction
    item_id UUID NOT NULL, -- FK to relevant table
    
    -- Issue description
    issue_category VARCHAR(50), -- missing_info/low_confidence/anomaly/policy_violation
    issue_description TEXT NOT NULL,
    ai_suggestion JSONB, -- What agent suggests
    ai_confidence INTEGER,
    ai_reasoning TEXT,
    
    -- Attachments
    related_documents UUID[], -- Array of document IDs
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending/in_review/resolved/escalated
    assigned_to UUID REFERENCES users(id),
    assigned_at TIMESTAMP,
    
    -- Resolution
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP,
    resolution JSONB, -- What human decided
    resolution_notes TEXT,
    
    -- Learning flag
    apply_to_similar BOOLEAN DEFAULT false, -- "Treat all similar cases like this"
    created_learning_rule BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_review_queue_status ON review_queue(client_id, status, priority);

-- Menneske-til-agent kommunikasjon
CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    review_queue_id UUID REFERENCES review_queue(id),
    
    -- Conversation thread
    message_sequence INTEGER NOT NULL,
    sender_type VARCHAR(20) NOT NULL, -- user/agent
    sender_id UUID,
    
    message TEXT NOT NULL,
    
    -- If agent is asking for clarification
    requires_response BOOLEAN DEFAULT false,
    response_deadline TIMESTAMP,
    
    timestamp TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(review_queue_id, message_sequence)
);

-- Feedback og læring
CREATE TABLE human_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_queue_id UUID REFERENCES review_queue(id),
    agent_decision_id UUID REFERENCES agent_decisions(id),
    
    -- Feedback
    feedback_type VARCHAR(50) NOT NULL, -- correction/confirmation/rule/explanation
    instruction TEXT NOT NULL, -- "Book these invoices like..."
    
    -- Scope
    apply_scope VARCHAR(20) NOT NULL, -- this_only/all_similar/always
    scope_filter JSONB, -- Criteria for "all_similar" (vendor, amount range, etc)
    
    -- Learning impact
    created_learning_rule BOOLEAN DEFAULT false,
    learning_rule_id UUID, -- FK to agent_learned_patterns if rule was created
    
    given_by UUID REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**💡 MITT FORSLAG:**
- `issue_category` - kategoriser type problem for analyse
- `due_date` - SLA-håndtering
- `agent_conversations` - toveis dialog mellom agent og regnskapsfører!
- `apply_scope` med `scope_filter` - fleksibel måte å si "gjør dette for alle leverandører i kategori X"
- `related_documents` array - lett tilgang til relevant dokumentasjon

---

## 📊 QUALITY SYSTEM & COMPLIANCE

```sql
-- Kvalitetssystem sjekklister
CREATE TABLE quality_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id), -- Template per tenant
    
    template_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL, -- month_end/quarter_end/year_end/vat_report/audit_prep
    
    -- Checklist items
    checklist JSONB NOT NULL, -- Array of {task, description, required, estimated_time}
    
    -- Triggers
    auto_create_trigger VARCHAR(50), -- end_of_month/end_of_quarter/manual
    advance_notice_days INTEGER DEFAULT 5,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Konkrete kvalitetsoppgaver
CREATE TABLE quality_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    template_id UUID REFERENCES quality_templates(id),
    
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    
    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    due_date DATE NOT NULL,
    
    -- Checklist progress
    checklist JSONB NOT NULL, -- Items from template
    completed_items JSONB, -- Array of {task_id, completed_by, completed_at, notes}
    
    -- Status
    status VARCHAR(20) DEFAULT 'not_started', -- not_started/in_progress/completed/overdue
    progress_percentage INTEGER DEFAULT 0,
    
    -- Assignment
    responsible_user UUID REFERENCES users(id),
    assigned_at TIMESTAMP,
    
    -- Agent assistance
    ai_can_assist BOOLEAN DEFAULT true,
    ai_completed_items UUID[], -- Tasks agent completed
    
    -- Completion
    completed_at TIMESTAMP,
    approved_by UUID REFERENCES users(id),
    approval_notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- SLA tracking mellom byrå og kunde
CREATE TABLE sla_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Agreement details
    agreement_name VARCHAR(255),
    
    -- Service levels
    invoice_booking_deadline_hours INTEGER DEFAULT 24,
    reconciliation_deadline_days INTEGER DEFAULT 5,
    month_end_deadline_days INTEGER DEFAULT 10,
    response_time_hours INTEGER DEFAULT 4,
    
    -- Penalties/bonuses (optional)
    late_penalty_enabled BOOLEAN DEFAULT false,
    penalty_terms JSONB,
    
    is_active BOOLEAN DEFAULT true,
    effective_from DATE NOT NULL,
    effective_to DATE,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- SLA performance tracking
CREATE TABLE sla_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sla_agreement_id UUID REFERENCES sla_agreements(id),
    
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Metrics
    total_invoices INTEGER,
    invoices_on_time INTEGER,
    avg_booking_time_hours DECIMAL(8,2),
    
    reconciliations_on_time INTEGER,
    reconciliations_total INTEGER,
    
    month_ends_on_time INTEGER,
    month_ends_total INTEGER,
    
    -- Overall score
    sla_compliance_percentage DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

**💡 MITT FORSLAG:**
- `quality_templates` - gjenbrukbare sjekklister
- `auto_create_trigger` - automatisk opprette oppgaver ved periodeslutt
- `ai_completed_items` - spor hva agenten gjorde vs menneske
- `sla_agreements` - formalisere avtaler
- `sla_performance` - automatisk måling av SLA-oppnåelse

---

## 🏛️ ALTINN & VAT REPORTING

```sql
-- MVA-meldinger
CREATE TABLE vat_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE RESTRICT,
    
    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    vat_term VARCHAR(20) NOT NULL, -- monthly/bimonthly/annual
    
    -- Report data (structured per MVA-melding format)
    report_data JSONB NOT NULL, -- Complete MVA-melding structure
    
    -- Calculations
    vat_to_pay DECIMAL(15,2), -- Positive if we owe
    vat_to_reclaim DECIMAL(15,2), -- Positive if we get money back
    net_vat DECIMAL(15,2), -- Negative = reclaim, Positive = pay
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft', -- draft/submitted/accepted/rejected/paid
    
    -- Altinn submission
    altinn_reference VARCHAR(255),
    submitted_at TIMESTAMP,
    submitted_by UUID REFERENCES users(id), -- Who did BankID
    
    -- Response from Altinn
    altinn_response JSONB,
    acceptance_date TIMESTAMP,
    rejection_reason TEXT,
    
    -- Payment
    payment_due_date DATE,
    paid_at TIMESTAMP,
    payment_reference VARCHAR(255),
    
    -- Audit
    generated_by_type VARCHAR(20), -- ai_agent/user
    generated_at TIMESTAMP,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Altinn other reports (årsregnskap, etc) - for fremtiden
CREATE TABLE altinn_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE RESTRICT,
    
    submission_type VARCHAR(50) NOT NULL, -- annual_accounts/tax_return/other
    form_code VARCHAR(50), -- Altinn form code
    
    submission_data JSONB NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',
    altinn_reference VARCHAR(255),
    
    submitted_at TIMESTAMP,
    submitted_by UUID REFERENCES users(id),
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

**💡 MITT FORSLAG:**
- `vat_to_pay` og `vat_to_reclaim` separate felter - klarere oversikt
- `altinn_submissions` generisk tabell for fremtidige rapporter
- `reviewed_by` - krever alltid human review før innsending

---

## 📎 DOCUMENT STORAGE

```sql
-- Dokumenter (PDFs, bilder, EHF XMLs)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE RESTRICT,
    
    -- File info
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- pdf/xml/image/excel
    mime_type VARCHAR(100),
    file_size_bytes BIGINT,
    
    -- Storage (AWS S3)
    s3_bucket VARCHAR(100),
    s3_key VARCHAR(500),
    s3_region VARCHAR(50),
    
    -- Content hash for integrity & deduplication
    sha256_hash VARCHAR(64),
    
    -- OCR/AI processing
    ocr_text TEXT, -- Extracted text if OCR was run
    ai_extracted_data JSONB, -- Structured data extracted by AI
    ai_document_type VARCHAR(50), -- invoice/receipt/contract/other
    
    -- Metadata
    document_date DATE,
    related_entity_type VARCHAR(50), -- vendor_invoice/customer_invoice/bank_transaction
    related_entity_id UUID,
    
    -- Retention (Norwegian law = 5 years for accounting docs)
    retention_required_until DATE,
    archived BOOLEAN DEFAULT false,
    
    -- Upload tracking
    uploaded_by_type VARCHAR(20), -- ai_agent/user/ehf_system
    uploaded_by_id UUID,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    
    -- Access control
    is_sensitive BOOLEAN DEFAULT false,
    access_restricted_to UUID[], -- Array of user IDs
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_documents_client ON documents(client_id, created_at);
CREATE INDEX idx_documents_hash ON documents(sha256_hash); -- For deduplication
CREATE INDEX idx_documents_related ON documents(related_entity_type, related_entity_id);
```

**💡 MITT FORSLAG:**
- `sha256_hash` - deduplisering og integritet
- `ocr_text` og `ai_extracted_data` - lagre AI-prosessering
- `retention_required_until` - automatisk håndtering av lovpålagt oppbevaring
- `access_restricted_to` - noen dokumenter kan være ekstra sensitive

---

## 🔐 AGENT SESSIONS & MONITORING

```sql
-- Agent-økter (for sporing og debugging)
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Session info
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- What agent did
    tasks_attempted INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0,
    tasks_sent_to_review INTEGER DEFAULT 0,
    
    -- Resources used
    total_api_calls INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    estimated_cost_usd DECIMAL(10,4),
    
    -- Performance
    avg_confidence_score INTEGER,
    avg_processing_time_ms INTEGER,
    
    -- Errors
    errors_encountered JSONB, -- Array of errors
    
    session_summary TEXT
);

-- System metrics for dashboard
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    metric_date DATE NOT NULL,
    metric_hour INTEGER, -- 0-23, NULL for daily metrics
    
    -- Overall stats
    total_clients INTEGER,
    active_clients INTEGER,
    total_users INTEGER,
    
    -- Processing volume
    invoices_processed INTEGER,
    invoices_auto_approved INTEGER,
    invoices_sent_to_review INTEGER,
    
    bank_transactions_processed INTEGER,
    bank_transactions_auto_matched INTEGER,
    
    reconciliations_completed INTEGER,
    reconciliations_with_discrepancies INTEGER,
    
    -- Agent performance
    ai_avg_confidence INTEGER,
    ai_accuracy_rate DECIMAL(5,2), -- Based on human feedback
    
    -- Review queue
    review_queue_size INTEGER,
    avg_review_time_minutes INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(metric_date, metric_hour)
);
```

**💡 MITT FORSLAG:**
- `agent_sessions` - viktig for debugging og kostnadskontroll
- `estimated_cost_usd` - spor faktisk compute cost
- `system_metrics` - for dashboards og analytics
- `ai_accuracy_rate` - automatisk beregning basert på human feedback

---

## 💱 CURRENCY & EXCHANGE RATES

```sql
-- Supported currencies
CREATE TABLE currencies (
    currency_code CHAR(3) PRIMARY KEY, -- ISO 4217
    currency_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10),
    decimal_places INTEGER DEFAULT 2,
    is_active BOOLEAN DEFAULT true
);

-- Populate initial currencies
INSERT INTO currencies (currency_code, currency_name, symbol, decimal_places) VALUES
('NOK', 'Norwegian Krone', 'kr', 2),
('EUR', 'Euro', '€', 2),
('USD', 'US Dollar', '$', 2),
('DKK', 'Danish Krone', 'kr', 2),
('SEK', 'Swedish Krona', 'kr', 2);

-- Exchange rates (daily updates from external API)
CREATE TABLE exchange_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rate_date DATE NOT NULL,
    from_currency CHAR(3) REFERENCES currencies(currency_code),
    to_currency CHAR(3) REFERENCES currencies(currency_code),
    rate DECIMAL(15,6) NOT NULL, -- E.g., 1 EUR = 11.234567 NOK
    source VARCHAR(50), -- norges_bank/ecb/manual
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(rate_date, from_currency, to_currency)
);

CREATE INDEX idx_exchange_rates_date ON exchange_rates(rate_date, from_currency, to_currency);

-- Update clients table to support base currency
ALTER TABLE clients ADD COLUMN base_currency CHAR(3) DEFAULT 'NOK' REFERENCES currencies(currency_code);

-- Update general_ledger_lines to support multiple currencies
ALTER TABLE general_ledger_lines ADD COLUMN currency CHAR(3) DEFAULT 'NOK' REFERENCES currencies(currency_code);
ALTER TABLE general_ledger_lines ADD COLUMN exchange_rate DECIMAL(15,6); -- Rate used at transaction time
ALTER TABLE general_ledger_lines ADD COLUMN amount_in_base_currency DECIMAL(15,2); -- Converted to client's base currency

-- Update vendor_invoices for multi-currency
ALTER TABLE vendor_invoices ADD COLUMN currency CHAR(3) DEFAULT 'NOK' REFERENCES currencies(currency_code);
ALTER TABLE vendor_invoices ADD COLUMN exchange_rate DECIMAL(15,6);
ALTER TABLE vendor_invoices ADD COLUMN amount_excl_vat_base_currency DECIMAL(15,2);
ALTER TABLE vendor_invoices ADD COLUMN total_amount_base_currency DECIMAL(15,2);

-- Update customer_invoices for multi-currency
ALTER TABLE customer_invoices ADD COLUMN currency CHAR(3) DEFAULT 'NOK' REFERENCES currencies(currency_code);
ALTER TABLE customer_invoices ADD COLUMN exchange_rate DECIMAL(15,6);
ALTER TABLE customer_invoices ADD COLUMN amount_excl_vat_base_currency DECIMAL(15,2);
ALTER TABLE customer_invoices ADD COLUMN total_amount_base_currency DECIMAL(15,2);

-- Update bank_transactions for multi-currency
ALTER TABLE bank_transactions ADD COLUMN currency CHAR(3) DEFAULT 'NOK' REFERENCES currencies(currency_code);
ALTER TABLE bank_transactions ADD COLUMN exchange_rate DECIMAL(15,6);
ALTER TABLE bank_transactions ADD COLUMN amount_base_currency DECIMAL(15,2);

-- Currency revaluation entries (unrealized gains/losses at period end)
CREATE TABLE currency_revaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE RESTRICT,
    
    revaluation_date DATE NOT NULL,
    period VARCHAR(7) NOT NULL, -- YYYY-MM
    
    account_number VARCHAR(10) NOT NULL, -- Foreign currency account
    original_currency CHAR(3) NOT NULL,
    
    balance_foreign_currency DECIMAL(15,2),
    original_exchange_rate DECIMAL(15,6),
    revaluation_exchange_rate DECIMAL(15,6),
    
    -- Calculated differences
    unrealized_gain_loss DECIMAL(15,2), -- Positive = gain, Negative = loss
    
    -- Resulting GL entry
    general_ledger_id UUID REFERENCES general_ledger(id),
    
    created_by VARCHAR(20) DEFAULT 'ai_agent',
    created_at TIMESTAMP DEFAULT NOW()
);
```

**💡 CURRENCY HANDLING FEATURES:**

1. **Automatic Exchange Rate Updates:**
   - Daily fetch from Norges Bank API (or ECB for EUR)
   - Stored in `exchange_rates` table
   - Agent uses rate from transaction date

2. **Dual Amount Storage:**
   - All transactions store both original currency AND base currency (NOK)
   - Makes reporting much easier
   - `exchange_rate` stored for audit trail

3. **Currency Revaluation:**
   - At month/quarter/year end, agent revalues foreign currency accounts
   - Creates adjustment entries for unrealized gains/losses
   - Required for accurate financial statements

4. **Agent Logic for Currency:**
```
When booking foreign invoice:
1. Get exchange rate for invoice_date
2. Convert to base currency (NOK)
3. Store both amounts
4. If rate unavailable: Send to review_queue

At month-end:
1. Find all foreign currency accounts
2. Get closing rate
3. Calculate unrealized gain/loss
4. Create revaluation GL entry
```

---

## 💾 ADDITIONAL TABLES (Future Expansion)

```sql
-- Dimensjoner (avdelinger, prosjekter, kostsentere)
CREATE TABLE dimensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    
    dimension_type VARCHAR(50) NOT NULL, -- department/project/cost_center/custom
    dimension_code VARCHAR(50) NOT NULL,
    dimension_name VARCHAR(255) NOT NULL,
    
    parent_dimension_id UUID REFERENCES dimensions(id), -- For hierarchy
    
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(client_id, dimension_type, dimension_code)
);

-- VAT codes (Norwegian MVA-koder)
CREATE TABLE vat_codes (
    code VARCHAR(10) PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    rate DECIMAL(5,2) NOT NULL, -- E.g., 25.00 for 25%
    account_number_sales VARCHAR(10), -- Which account for sales
    account_number_purchase VARCHAR(10), -- Which account for purchases
    is_active BOOLEAN DEFAULT true
);

-- Populate with Norwegian VAT codes
INSERT INTO vat_codes (code, description, rate, account_number_sales, account_number_purchase) VALUES
('3', 'Utgående mva. høy sats', 25.00, '2700', '2740'),
('31', 'Utgående mva. middels sats', 15.00, '2710', '2741'),
('32', 'Utgående mva. lav sats', 12.00, '2711', '2742'),
('33', 'Utgående mva. lav sats, matservering', 15.00, '2712', NULL),
('5', 'Inngående mva. høy sats', 25.00, NULL, '2740'),
('51', 'Inngående mva. middels sats', 15.00, NULL, '2741'),
('52', 'Inngående mva. lav sats', 12.00, NULL, '2742'),
('6', 'Ingen MVA-plikt', 0.00, '2750', '2750');

-- Notifications system
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    recipient_type VARCHAR(20) NOT NULL, -- user/client/tenant
    recipient_id UUID NOT NULL,
    
    notification_type VARCHAR(50) NOT NULL, -- review_needed/payment_due/bankid_required/error/info
    priority VARCHAR(20) DEFAULT 'normal',
    
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    related_item_type VARCHAR(50),
    related_item_id UUID,
    
    read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    
    action_required BOOLEAN DEFAULT false,
    action_url VARCHAR(500),
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_recipient ON notifications(recipient_type, recipient_id, read);
```

---

## 🎯 INDEXES & CONSTRAINTS

```sql
-- Performance indexes
CREATE INDEX idx_gl_client_period ON general_ledger(client_id, period);
CREATE INDEX idx_gl_date ON general_ledger(client_id, accounting_date);
CREATE INDEX idx_gl_source ON general_ledger(source_type, source_id);

CREATE INDEX idx_vendor_invoices_status ON vendor_invoices(client_id, review_status, payment_status);
CREATE INDEX idx_vendor_invoices_date ON vendor_invoices(client_id, invoice_date);

CREATE INDEX idx_bank_trans_date ON bank_transactions(bank_account_id, transaction_date);
CREATE INDEX idx_bank_trans_match ON bank_transactions(matched_invoice_type, matched_invoice_id);

CREATE INDEX idx_review_queue_assigned ON review_queue(assigned_to, status);

-- Foreign key constraints already defined above

-- Check constraints
ALTER TABLE general_ledger_lines ADD CONSTRAINT check_debit_credit
    CHECK (debit_amount >= 0 AND credit_amount >= 0);

ALTER TABLE general_ledger_lines ADD CONSTRAINT check_not_both
    CHECK (NOT (debit_amount > 0 AND credit_amount > 0));
```

---

## 📊 VIEWS (for reporting)

```sql
-- Trial balance view
CREATE VIEW v_trial_balance AS
SELECT 
    c.id AS client_id,
    c.name AS client_name,
    gl.period,
    gl.fiscal_year,
    coa.account_number,
    coa.account_name,
    coa.account_type,
    SUM(gll.debit_amount) AS total_debit,
    SUM(gll.credit_amount) AS total_credit,
    SUM(gll.debit_amount) - SUM(gll.credit_amount) AS balance
FROM clients c
JOIN general_ledger gl ON c.id = gl.client_id
JOIN general_ledger_lines gll ON gl.id = gll.general_ledger_id
JOIN chart_of_accounts coa ON gll.account_number = coa.account_number AND c.id = coa.client_id
WHERE gl.status = 'posted' AND NOT gl.is_reversed
GROUP BY c.id, c.name, gl.period, gl.fiscal_year, coa.account_number, coa.account_name, coa.account_type;

-- Vendor balance view (reskontro)
CREATE VIEW v_vendor_balances AS
SELECT 
    c.id AS client_id,
    v.id AS vendor_id,
    v.vendor_number,
    v.name AS vendor_name,
    COUNT(vi.id) AS total_invoices,
    COUNT(CASE WHEN vi.payment_status = 'unpaid' THEN 1 END) AS unpaid_invoices,
    SUM(CASE WHEN vi.payment_status = 'unpaid' THEN vi.total_amount ELSE 0 END) AS unpaid_amount,
    SUM(CASE WHEN vi.payment_status = 'overdue' THEN vi.total_amount ELSE 0 END) AS overdue_amount
FROM clients c
JOIN vendors v ON c.id = v.client_id
LEFT JOIN vendor_invoices vi ON v.id = vi.vendor_id
GROUP BY c.id, v.id, v.vendor_number, v.name;

-- AI performance dashboard view
CREATE VIEW v_ai_performance AS
SELECT 
    DATE(ad.timestamp) AS date,
    ad.decision_type,
    COUNT(*) AS total_decisions,
    AVG(ad.confidence_score) AS avg_confidence,
    COUNT(CASE WHEN ad.correct = true THEN 1 END) AS correct_decisions,
    COUNT(CASE WHEN ad.human_override = true THEN 1 END) AS human_overrides,
    ROUND(100.0 * COUNT(CASE WHEN ad.correct = true THEN 1 END) / COUNT(*), 2) AS accuracy_rate
FROM agent_decisions ad
WHERE ad.timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(ad.timestamp), ad.decision_type;
```

---

## 🔄 CRITICAL WORKFLOWS TO IMPLEMENT

### 1. EHF Invoice Processing
```
EHF arrives → Parse XML → Extract data → Create vendor_invoice record
→ AI analyzes invoice → Suggests booking → 
   IF confidence >= threshold: Auto-book to general_ledger
   ELSE: Send to review_queue
→ Store PDF in documents → Link to GL entry
```

### 2. Bank Transaction Matching
```
Import bank transactions → For each transaction:
   - Check for KID match → customer_invoices
   - Check amount/date match → vendor_invoices or customer_invoices
   - AI suggests account if no match
   - IF confident: Auto-book
   - ELSE: review_queue
```

### 3. Month-End Reconciliation
```
Create reconciliation_task → Agent compares:
   - Bank statement vs GL bank account
   - Vendor sub-ledger vs GL vendor account
   - Customer sub-ledger vs GL customer account
→ Generate reconciliation_results
→ IF discrepancies: Create reconciliation_actions
→ Send to review_queue if needed
```

### 4. VAT Report Generation
```
At period end → Create quality_task for VAT
→ Agent calculates VAT from GL entries
→ Generate vat_report (draft)
→ Send to review_queue (always requires human approval)
→ Accountant reviews → Clicks "Ready for BankID"
→ Agent initiates BankID flow
→ User approves → Submit to Altinn API
```

### 5. Learning Loop
```
Human corrects agent decision → Store in human_feedback
→ Update agent_decisions.correct field
→ Analyze pattern → If recurring: Create agent_learned_patterns
→ Apply to future similar cases
```

---

## 🚀 DEPLOYMENT PLAN (AWS Oslo - eu-north-1)

### Infrastructure Setup:

```yaml
Region: eu-north-1 (Stockholm) # Oslo via Stockholm datacenter
Availability Zones: 3 (eu-north-1a, eu-north-1b, eu-north-1c)

Database:
  Service: Amazon RDS PostgreSQL 16
  Instance: db.r6g.xlarge (start) → scale up as needed
  Storage: 500GB gp3 (provisioned IOPS: 12,000)
  Multi-AZ: Yes (high availability)
  Backup: 
    - Automated daily backups (7 day retention)
    - Manual snapshots before major changes
  Encryption: At rest (AWS KMS) + in transit (SSL/TLS)
  
Application Layer:
  Service: AWS ECS Fargate (containerized)
  Containers:
    - API Gateway (GraphQL/REST)
    - Orchestrator Agent Service
    - Invoice Agent Service
    - Bank Agent Service
    - Reconciliation Agent Service
    - Background Job Workers (for scheduled tasks)
  
  Load Balancer: Application Load Balancer (ALB)
  Auto-scaling: Based on CPU/Memory metrics

File Storage:
  Service: Amazon S3
  Buckets:
    - erp-documents-prod (PDFs, XMLs, images)
    - erp-backups
    - erp-logs
  Lifecycle: 
    - Standard → Intelligent-Tiering after 30 days
    - Archive to Glacier after 2 years (legal requirement)
    - Delete after 6 years (beyond legal requirement)
  
  Encryption: Server-side (SSE-S3)
  Versioning: Enabled (protect against accidental deletion)

Caching:
  Service: Amazon ElastiCache (Redis)
  Use cases:
    - Exchange rate caching (1 hour TTL)
    - Agent learned patterns (5 min TTL)
    - User session data
    - Frequently accessed chart of accounts

Message Queue:
  Service: Amazon SQS
  Queues:
    - ehf-incoming-queue (EHF invoices to process)
    - bank-import-queue (Bank transactions)
    - reconciliation-queue (Scheduled reconciliations)
    - notification-queue (Email/SMS notifications)
    - review-queue-alerts (High-priority items)

AI/ML:
  Service: AWS Bedrock (Claude API via Bedrock)
  Model: Claude Sonnet 4.5
  Fallback: Direct Anthropic API if Bedrock unavailable
  
  Cost optimization:
    - Cache common prompts (Redis)
    - Batch process when possible
    - Use confidence thresholds to minimize calls

Monitoring:
  Service: Amazon CloudWatch
  Metrics:
    - API response times
    - Agent processing times
    - Database query performance
    - Queue depths
    - Error rates
    - Cost per client
  
  Alarms:
    - High error rate (> 5%)
    - Database CPU > 80%
    - Queue depth > 1000 items
    - Cost spike (> 20% daily increase)

Security:
  - VPC with private subnets for database
  - Security groups (strict ingress/egress rules)
  - AWS WAF (Web Application Firewall)
  - Secrets Manager for API keys, DB credentials
  - IAM roles (least privilege principle)
  - CloudTrail (audit all AWS API calls)

Compliance:
  - GDPR compliant (data in EU)
  - SOC 2 considerations
  - Norwegian Accounting Act compliance
  - 5-year data retention for accounting docs
```

### Cost Estimate (Monthly, per 100 clients):

```
RDS PostgreSQL:        $500
ECS Fargate:           $400
S3 Storage (500GB):    $12
ElastiCache:           $150
CloudWatch:            $50
Data Transfer:         $100
Bedrock/Claude API:    $2,000 (varies with usage)
---
Total:                 ~$3,200/month

Per client cost:       $32/month
(Can charge $50-100/month for profit margin)
```

### Data Residency & GDPR:

✅ All data stored in EU (Stockholm datacenter)
✅ Customer data not transferred outside EU
✅ Right to erasure: Implemented via tenant/client deletion
✅ Data portability: Export to JSON/CSV via API
✅ Encryption at rest and in transit

---

## 🚀 PHASE 1 IMPLEMENTATION PLAN

### Scope: Leverandørfakturaer (EHF + PDF) og Utlegg

**Duration:** 3-4 måneder  
**Goal:** Få ett regnskapsbyrå med 10 klienter til å bruke systemet i produksjon

---

### Month 1: Foundation

**Week 1-2: Database & Infrastructure**
- ✅ Set up AWS account (eu-north-1)
- ✅ Deploy PostgreSQL RDS
- ✅ Create all core tables:
  - tenants, clients, users
  - chart_of_accounts
  - general_ledger + lines
  - vendors + vendor_invoices
  - documents
  - audit_trail
  - agent_decisions
  - review_queue
  - human_feedback
- ✅ Set up S3 buckets for documents
- ✅ Configure CloudWatch monitoring

**Week 3-4: API Layer**
- Build GraphQL API (or REST if preferred)
- Endpoints:
  - Authentication (JWT)
  - Client management
  - Vendor CRUD
  - Invoice upload (PDF)
  - Document storage
  - Review queue management
- Unit tests for all endpoints

---

### Month 2: Agent Development

**Week 1-2: Invoice Agent**
```python
InvoiceAgent capabilities:
1. Parse PDF invoices (OCR via AWS Textract)
2. Extract: vendor, date, amount, VAT, line items
3. Match to existing vendor (or suggest new)
4. Suggest GL accounts based on:
   - Invoice description
   - Vendor history
   - Learned patterns
5. Calculate confidence score
6. If confidence >= 85%: Auto-book
   Else: Send to review_queue
```

**Week 3: EHF Integration**
- Set up Pepol access point (e.g., Unimicro or Visma)
- Build EHF receiver webhook
- Parse EHF XML format
- Create vendor_invoice from EHF data
- Store original XML + PDF
- Trigger Invoice Agent

**Week 4: Orchestrator Agent**
```python
Orchestrator capabilities:
1. Receive new invoice (EHF or PDF)
2. Delegate to Invoice Agent
3. Check agent_learned_patterns for similar cases
4. Make final decision: Auto-book or Review
5. Log decision to agent_decisions
6. Update system_metrics
```

---

### Month 3: Review Interface & Learning

**Week 1-2: Accountant Dashboard (Web)**
```
Dashboard features:
- Multi-tenant client selector
- Review queue (prioritized by due date)
- Invoice details view:
  - PDF preview
  - AI suggestion
  - Confidence score
  - AI reasoning
  - Edit form
- Actions:
  - Approve AI suggestion
  - Override and correct
  - Add feedback: "Apply to similar" checkbox
  - Chat with agent (text input)
- Batch operations: Approve multiple invoices
```

**Week 3: Learning Loop**
```python
When accountant corrects:
1. Store in human_feedback
2. Mark agent_decision.correct = true/false
3. If "apply to similar" checked:
   - Analyze pattern
   - Create agent_learned_patterns entry
   - Apply to all pending similar invoices
4. Retrain agent on next iteration
```

**Week 4: Utlegg (Expense Reports)**
```sql
-- Add expense_reports table
CREATE TABLE expense_reports (
    id UUID PRIMARY KEY,
    client_id UUID,
    employee_name VARCHAR(255),
    report_date DATE,
    total_amount DECIMAL(15,2),
    currency CHAR(3),
    status VARCHAR(20), -- draft/submitted/approved/booked
    
    -- Line items (JSONB for flexibility)
    line_items JSONB, -- [{description, amount, vat, category, receipt_id}]
    
    general_ledger_id UUID,
    ...
);

-- Agent handles expense reports similarly to invoices
```

---

### Month 4: Testing & Pilot

**Week 1: Integration Testing**
- End-to-end scenarios:
  1. EHF arrives → Agent books → Verified in GL
  2. PDF upload → Low confidence → Review queue → Accountant corrects → Agent learns
  3. Expense report → Agent suggests split booking → Approved
- Load testing: 1000 invoices/day

**Week 2: Security & Compliance**
- Penetration testing
- GDPR compliance audit
- Accounting Act compliance verification
- Backup/restore testing

**Week 3-4: Pilot with 1 Accounting Firm**
- Onboard 10 clients
- Train accountants (2-hour workshop)
- Daily support and monitoring
- Collect feedback
- Measure:
  - % invoices auto-booked
  - Time saved per invoice
  - Accountant satisfaction
  - Error rate

---

### Success Metrics (Phase 1):

```
Target after 4 months:

1. Agent auto-books 70%+ of invoices
2. Average confidence score: 90%+
3. Error rate: < 2%
4. Time per invoice: 30 seconds (vs 3 minutes manual)
5. Accountant satisfaction: 8/10 or higher
6. Learning: Agent improves 5% monthly
```

---

### Phase 2 (Months 5-8): Bank Integration

```
Month 5-6: Bank API Integration
- Connect to Norwegian banks (DNB, SpareBank1, etc.)
- Daily transaction import
- Bank Agent: Match transactions to invoices
- Payment queue with BankID flow

Month 7-8: Reconciliation
- Reconciliation Agent
- Bank vs GL reconciliation
- Automated discrepancy detection
- Suggested correction entries
```

---

### Phase 3 (Months 9-12): Customer Invoicing & VAT

```
Month 9-10: Customer Portal
- Customers can view their accounting status
- Submit customer invoices for booking
- View reports (P&L, balance sheet)

Month 11-12: VAT & Altinn
- VAT report generation
- BankID integration for Altinn submission
- Quality system & compliance checklists
```

---

## 🛠️ TECHNOLOGY STACK

### Backend:
```
Language: Python 3.11
Framework: FastAPI (async, fast, modern)
ORM: SQLAlchemy 2.0
Database: PostgreSQL 16
Caching: Redis
Queue: Celery + SQS
AI: Anthropic Claude API (via AWS Bedrock)
```

### Frontend (Accountant Dashboard):
```
Framework: React 18 + TypeScript
UI Library: shadcn/ui (modern, accessible)
State: TanStack Query (React Query)
Forms: React Hook Form + Zod validation
Charts: Recharts
PDF Viewer: react-pdf
```

### DevOps:
```
IaC: Terraform (define all AWS resources)
CI/CD: GitHub Actions
Containers: Docker
Orchestration: AWS ECS Fargate
Monitoring: CloudWatch + Sentry (error tracking)
Logging: CloudWatch Logs + structured JSON
```

### Testing:
```
Unit: pytest (Python), Jest (React)
Integration: pytest with test database
E2E: Playwright
Load: Locust
```

---

## 💡 CRITICAL DECISIONS TO MAKE BEFORE STARTING:

1. **GraphQL vs REST API?**
   - GraphQL: More flexible, modern, single endpoint
   - REST: Simpler, more conventional
   - **My recommendation:** GraphQL (better for complex queries)

2. **Monolith vs Microservices?**
   - Start with **modular monolith** (simpler deployment)
   - Easy to split into microservices later if needed

3. **Agent hosting:**
   - Option A: Agent runs as part of API (same container)
   - Option B: Separate agent service (scales independently)
   - **My recommendation:** Option B (better scalability)

4. **Real-time vs Batch processing?**
   - EHF invoices: Real-time (webhook)
   - PDF uploads: Real-time
   - Bank transactions: Batch (nightly import)
   - Reconciliation: Scheduled (monthly)

5. **Chart of Accounts:**
   - Use standard Norwegian chart (NS 4102)?
   - Allow clients to customize?
   - **My recommendation:** Start with NS 4102, allow customization

---

## 🚀 NEXT STEPS

1. **Set up AWS RDS PostgreSQL instance**
2. **Run this schema** to create all tables
3. **Build API layer** (GraphQL or REST)
4. **Implement agent decision engine** (Claude API integration)
5. **Build review dashboard** (accountant interface)
6. **Start with ONE flow**: EHF → Auto-booking → Review queue

---

## 💭 MINE VIKTIGSTE FORSLAG:

1. **Cross-client læring** via `agent_learned_patterns` - dette gjør systemet smartere over tid
2. **Confidence scoring** på alle AI-beslutninger - transparent og trygt
3. **Toveis kommunikasjon** via `agent_conversations` - ikke bare varsler, faktisk dialog
4. **Scope-basert feedback** med `apply_scope` - effektiv læring
5. **Comprehensive audit trail** - alt logges, ingenting slettes
6. **SLA tracking** - måling av kvalitet og compliance
7. **Document retention** - automatisk håndtering av lovkrav
8. **Session tracking** - kostnadskontroll og debugging

Dette er et solid fundament. Hva tenker du?
