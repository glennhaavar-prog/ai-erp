# AI-Agent ERP - Backend

FastAPI + GraphQL backend for AI-agent-first ERP system.

---

## 📚 **NEW: Complete Setup Guide Available!**

**🔗 [See SETUP.md for comprehensive setup instructions](./SETUP.md)**

Includes:
- Step-by-step environment setup
- Dependency management with locked versions
- Troubleshooting guide
- Production deployment instructions

**Critical:** Dependencies are now locked to exact versions (see `requirements.txt`).  
Read [DEPENDENCY_LOCK_SUMMARY.md](./DEPENDENCY_LOCK_SUMMARY.md) for details.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your keys:
# - DATABASE_URL
# - ANTHROPIC_API_KEY
# - AWS credentials (if using S3/Textract)
```

### 3. Setup Database

```bash
# Start PostgreSQL (via Docker)
docker run -d \
  --name ai-erp-postgres \
  -e POSTGRES_DB=ai_erp \
  -e POSTGRES_USER=erp_user \
  -e POSTGRES_PASSWORD=erp_password \
  -p 5432:5432 \
  postgres:16

# Run migrations
alembic upgrade head
```

### 4. Run Development Server

```bash
# Start FastAPI
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access API

- **API Root**: http://localhost:8000
- **GraphQL Playground**: http://localhost:8000/graphql
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings & environment
│   ├── database.py             # SQLAlchemy setup
│   ├── models/                 # Database models
│   │   ├── tenant.py
│   │   ├── client.py
│   │   ├── vendor.py
│   │   ├── vendor_invoice.py
│   │   ├── general_ledger.py
│   │   └── ...
│   ├── graphql/                # GraphQL schema
│   │   ├── schema.py
│   │   ├── types/
│   │   ├── queries/
│   │   └── mutations/
│   ├── agents/                 # AI agents
│   │   ├── invoice_agent.py
│   │   └── orchestrator.py
│   ├── services/               # Business logic
│   │   ├── ocr_service.py
│   │   └── s3_service.py
│   └── tasks/                  # Celery background tasks
│       └── invoice_processing.py
├── tests/                      # Unit & integration tests
├── alembic/                    # Database migrations
├── requirements.txt
└── README.md
```

## 🗄️ Database Models

### Core Models
- **Tenant**: Regnskapsbyrå (accounting firm)
- **Client**: Klienter under byrå
- **User**: Regnskapsførere (accountants)

### Accounting
- **Account**: Chart of accounts (kontoplan)
- **GeneralLedger**: Journal entries (hovedbok)
- **GeneralLedgerLine**: Entry lines (debit/credit)

### Vendors & Invoices
- **Vendor**: Leverandører
- **VendorInvoice**: Incoming invoices

### AI & Learning
- **AgentDecision**: Log of AI decisions
- **AgentLearnedPattern**: Cross-client learning
- **ReviewQueue**: Human review queue

### Audit
- **AuditTrail**: Immutable audit log
- **Document**: PDF/XML storage metadata

## 🤖 Invoice Agent

```python
from app.agents.invoice_agent import InvoiceAgent

agent = InvoiceAgent()

result = await agent.analyze_invoice(
    ocr_text="FAKTURA\nLeverandør: Test AS\n...",
    client_id="uuid",
    vendor_history=None,
    learned_patterns=None
)

print(result['confidence_score'])  # 0-100
print(result['suggested_booking'])  # GL entries
```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_invoice_agent.py
```

## 🔒 Security

- JWT authentication
- Role-based access control (RBAC)
- Multi-tenant data isolation
- Audit trail on all changes
- Encrypted secrets (AWS Secrets Manager)

## 📊 GraphQL Examples

### Query Clients

```graphql
query GetClients {
  clients(tenantId: "uuid", limit: 10) {
    id
    name
    orgNumber
    aiConfidenceThreshold
    totalInvoices
    autoBookedPercentage
  }
}
```

### Create Client

```graphql
mutation CreateClient($input: ClientInput!) {
  createClient(input: $input) {
    id
    name
  }
}
```

## 🚧 TODO

- [ ] Implement all GraphQL queries/mutations
- [ ] Add authentication middleware
- [ ] Setup Celery workers
- [ ] AWS Textract OCR integration
- [ ] EHF XML parsing
- [ ] Bank reconciliation agent
- [ ] Real-time subscriptions (WebSocket)

## 📝 Development Notes

### Multi-tenant Filtering

**ALWAYS filter by tenant_id or client_id:**

```python
# ✅ CORRECT
query = select(Client).where(Client.tenant_id == current_user.tenant_id)

# ❌ WRONG - will leak data!
query = select(Client)
```

### Immutable Ledger

**NEVER delete or update GL entries:**

```python
# ✅ CORRECT - create reversal
reversal = GeneralLedger(
    description="Reversal of entry #123",
    is_reversed=True,
    ...
)

# ❌ WRONG
db.delete(old_entry)  # NEVER!
```

### Confidence-based Decisions

```python
if confidence >= client.ai_confidence_threshold:  # Default: 85%
    auto_book_invoice(invoice, suggestion)
else:
    send_to_review_queue(invoice, suggestion)
```

## 📞 Support

For issues or questions, contact Glenn or check the docs in `/docs`.
