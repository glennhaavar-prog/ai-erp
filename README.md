# 🚀 AI-Agent ERP System

**AI-agent-first ERP for Norwegian accounting firms**

**Status**: MVP Development - Foundation Complete  
**Target**: 6-8 weeks to pilot-ready  
**Last Updated**: 2. februar 2026, kl. 23:30

---

## 📊 Project Overview

Building a complete ERP system where AI agents are the primary interface, not humans.

**Differentiator**: Unlike Tripletex/PowerOffice (GUI-first), we're built FOR AI from day one.

### Target Market
- Norwegian accounting firms (regnskapsbyrå)
- Pilot: 4 clients
- Goal: 10,000+ clients

### MVP Scope (Phase 1)
- ✅ PDF invoice upload
- ✅ OCR with AWS Textract
- ✅ AI analysis (Claude API)
- ✅ Review queue for accountants
- ✅ Learning system (agent learns from feedback)
- ✅ Multi-tenant architecture

### Not in MVP
- ❌ EHF integration (comes later)
- ❌ Bank integration
- ❌ Customer portal
- ❌ Altinn/MVA reporting

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         AWS EC2 (OpenClaw)               │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴─────────┐
    │                    │
┌───▼────────┐    ┌──────▼──────┐
│ PostgreSQL │    │   AWS S3    │
│    RDS     │    │  (Docs)     │
└────────────┘    └─────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│         PYTHON BACKEND                   │
│  FastAPI + GraphQL + Celery              │
│                                          │
│  ┌────────────────────────────────┐     │
│  │   INVOICE AGENT (Claude API)   │     │
│  │   - OCR analysis               │     │
│  │   - Booking suggestions        │     │
│  │   - Confidence scoring         │     │
│  │   - Learning from feedback     │     │
│  └────────────────────────────────┘     │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│      REACT FRONTEND                      │
│  (Accountant Dashboard)                  │
│  - Review Queue                          │
│  - Invoice Viewer                        │
│  - "Apply to Similar" feature            │
└─────────────────────────────────────────┘
```

---

## 🎯 Tech Stack

### Backend
- **Language**: Python 3.11
- **Framework**: FastAPI (async)
- **GraphQL**: Strawberry GraphQL
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0
- **Queue**: Celery + Redis
- **AI**: Anthropic Claude API (Sonnet 4.5)
- **OCR**: AWS Textract
- **Storage**: AWS S3

### Frontend
- **Framework**: React 18 + TypeScript
- **UI**: shadcn/ui + Tailwind CSS
- **GraphQL Client**: Apollo Client
- **Forms**: React Hook Form + Zod

### Infrastructure
- **Cloud**: AWS (eu-north-1 - Stockholm/Oslo)
- **Containers**: Docker + ECS Fargate
- **IaC**: Terraform
- **CI/CD**: GitHub Actions

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16
- Redis 7
- Docker & Docker Compose (recommended)

### Local Development

```bash
# 1. Clone/navigate to project
cd ai-erp

# 2. Start services with Docker Compose
docker-compose up -d

# 3. Access API
open http://localhost:8000          # API root
open http://localhost:8000/graphql  # GraphQL playground

# 4. Check health
curl http://localhost:8000/health
```

### Manual Setup (without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python -m app.main

# Frontend (coming soon)
cd frontend
npm install
npm run dev
```

---

## 📁 Project Structure

```
ai-erp/
├── docs/                           # All documentation
│   ├── PROJECT_BRIEF.md            # Full project overview
│   ├── HANDOFF_TO_OPENCLAWD.md     # Implementation guide
│   ├── getting_started_guide.md    # Code examples
│   ├── erp_database_skisse.md      # Database design
│   └── agent_workflow_and_api.md   # Workflows & GraphQL schema
│
├── backend/                        # Python FastAPI backend
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── config.py               # Settings
│   │   ├── database.py             # SQLAlchemy setup
│   │   ├── models/                 # Database models (12 models)
│   │   ├── graphql/                # GraphQL schema
│   │   ├── agents/                 # AI agents
│   │   │   └── invoice_agent.py    # Invoice analysis AI
│   │   ├── services/               # Business logic
│   │   └── tasks/                  # Celery background tasks
│   ├── tests/                      # Unit & integration tests
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                       # React TypeScript frontend
│   └── src/                        # (structure ready, code TBD)
│
├── infrastructure/                 # Terraform IaC
│
├── docker-compose.yml              # Local dev environment
└── README.md                       # This file
```

---

## 🗄️ Database Models (Complete)

All 12 core models implemented:

### Multi-tenant
- ✅ **Tenant** - Regnskapsbyrå (accounting firms)
- ✅ **Client** - Kunder under byrå
- ✅ **User** - Regnskapsførere (accountants)

### Accounting Core
- ✅ **Account** - Chart of accounts (kontoplan NS 4102)
- ✅ **GeneralLedger** - Journal entries (hovedbok) - IMMUTABLE
- ✅ **GeneralLedgerLine** - Entry lines (debit/credit)

### Vendors & Invoices
- ✅ **Vendor** - Leverandører
- ✅ **VendorInvoice** - Incoming invoices (EHF + PDF)

### AI & Learning
- ✅ **AgentDecision** - Log of all AI decisions
- ✅ **AgentLearnedPattern** - Cross-client learning patterns
- ✅ **ReviewQueue** - Human review queue

### Audit & Documents
- ✅ **AuditTrail** - Immutable audit log (5-year retention)
- ✅ **Document** - PDF/XML storage metadata (S3)

---

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

# Returns:
# {
#   'vendor': {'name': 'Test AS', 'org_number': '123456789'},
#   'confidence_score': 92,
#   'suggested_booking': [
#     {'account': '6300', 'debit': 1000, 'description': '...'},
#     {'account': '2740', 'debit': 250, 'description': 'VAT'},
#     {'account': '2400', 'credit': 1250, 'description': 'Payable'}
#   ],
#   'reasoning': 'This invoice is from a known vendor...'
# }
```

---

## ✅ What's Done (Tonight)

### Backend Foundation (100%)
- ✅ Project structure created
- ✅ Python dependencies defined (requirements.txt)
- ✅ Config system (Pydantic Settings)
- ✅ Database setup (SQLAlchemy async)
- ✅ All 12 database models implemented
- ✅ FastAPI app with health check
- ✅ GraphQL schema structure
- ✅ Invoice Agent (Claude API integration)
- ✅ Docker Compose for local dev
- ✅ .gitignore and .env.example
- ✅ README documentation

### Code Quality
- ✅ Type hints throughout
- ✅ Docstrings on all models
- ✅ Logging configured
- ✅ Error handling
- ✅ Multi-tenant filtering built in
- ✅ Immutable ledger constraints

---

## 🚧 What's Next (Tomorrow + Week 1)

### Immediate (Glenn needs to provide)
1. **AWS Credentials** - for RDS, S3, Textract
2. **Claude API Key** - for Invoice Agent
3. **Sample invoices** - PDFs from pilot clients for testing

### Week 1 Tasks
1. **Database Setup**
   - Create RDS PostgreSQL instance
   - Run Alembic migrations
   - Seed with test data

2. **Complete GraphQL API**
   - Implement all queries (clients, vendors, invoices, review queue)
   - Implement mutations (create, update)
   - Add authentication middleware

3. **OCR Integration**
   - AWS Textract service
   - S3 upload/download
   - Document processing pipeline

4. **Celery Task Queue**
   - Background invoice processing
   - Email notifications
   - Scheduled jobs

5. **Testing**
   - Unit tests for models
   - Integration tests for Invoice Agent
   - Test with real invoices

---

## 🔒 Critical Principles (Built In)

### 1. Multi-tenant Isolation
```python
# ALWAYS filter by tenant_id
query = select(Client).where(Client.tenant_id == current_user.tenant_id)
```

### 2. Immutable Ledger
```python
# Database constraints prevent updates/deletes on GL entries
# Only reversals allowed
```

### 3. Confidence-based Routing
```python
if confidence >= client.ai_confidence_threshold:  # Default: 85%
    auto_book_invoice()
else:
    send_to_review_queue()
```

### 4. Cross-client Learning
```python
# AgentLearnedPattern applies to multiple clients
# Success rate tracked and improved over time
```

### 5. Complete Audit Trail
```python
# Every change logged with who/what/when/why
# 5-year retention for Norwegian compliance
```

---

## 📊 Success Metrics (MVP)

**Target for 4 pilot clients:**
- ✅ 70%+ invoices auto-booked
- ✅ 90%+ average confidence score
- ✅ <2% error rate
- ✅ <30 seconds processing time per invoice
- ✅ 8/10 accountant satisfaction

---

## 📞 Support & Contact

**Project Owner**: Glenn Håvar Brottveit  
**Developer**: Nikoline (via OpenClaw)  
**Documentation**: See `/docs` folder

---

## 📝 License

Proprietary - All rights reserved
