# AI-Agent ERP: Oppstartsguide & Kodeeksempler
**Fra null til produksjon på 4 måneder**

---

## 🎯 TECH STACK (Valgt for 10,000+ klienter)

```yaml
Backend:
  Language: Python 3.11
  Framework: FastAPI (async, rask, moderne)
  GraphQL: Strawberry GraphQL (Python-native, type-safe)
  Database: PostgreSQL 16 + SQLAlchemy 2.0
  Caching: Redis 7
  Queue: Celery + AWS SQS
  AI: Anthropic Claude API via AWS Bedrock

Frontend (Accountant Dashboard):
  Framework: React 18 + TypeScript
  Build: Vite
  UI: shadcn/ui + Tailwind CSS
  State: TanStack Query (React Query)
  GraphQL Client: urql eller Apollo Client
  Forms: React Hook Form + Zod
  PDF Viewer: react-pdf

DevOps:
  Cloud: AWS (eu-north-1)
  IaC: Terraform
  CI/CD: GitHub Actions
  Containers: Docker + AWS ECS Fargate
  Monitoring: CloudWatch + Sentry
```

---

## 📁 PROJECT STRUCTURE

```
ai-erp/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Environment config
│   │   ├── database.py             # SQLAlchemy setup
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py
│   │   │   ├── client.py
│   │   │   ├── general_ledger.py
│   │   │   ├── vendor.py
│   │   │   └── ...
│   │   ├── graphql/                # GraphQL schema
│   │   │   ├── __init__.py
│   │   │   ├── schema.py           # Root schema
│   │   │   ├── types/              # GraphQL types
│   │   │   ├── queries/            # Query resolvers
│   │   │   ├── mutations/          # Mutation resolvers
│   │   │   └── subscriptions/      # Subscription resolvers
│   │   ├── agents/                 # AI agents
│   │   │   ├── orchestrator.py
│   │   │   ├── invoice_agent.py
│   │   │   ├── bank_agent.py
│   │   │   ├── reconciliation_agent.py
│   │   │   └── learning_engine.py
│   │   ├── services/               # Business logic
│   │   │   ├── invoice_service.py
│   │   │   ├── ocr_service.py
│   │   │   ├── ehf_service.py
│   │   │   ├── s3_service.py
│   │   │   └── ...
│   │   ├── tasks/                  # Celery background tasks
│   │   │   ├── invoice_processing.py
│   │   │   ├── reconciliation.py
│   │   │   └── scheduled.py
│   │   └── utils/
│   │       ├── auth.py
│   │       ├── helpers.py
│   │       └── exceptions.py
│   ├── tests/
│   ├── alembic/                    # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui components
│   │   │   ├── ReviewQueue.tsx
│   │   │   ├── InvoiceViewer.tsx
│   │   │   ├── AgentChat.tsx
│   │   │   └── ...
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ReviewQueue.tsx
│   │   │   ├── ClientView.tsx
│   │   │   └── Analytics.tsx
│   │   ├── graphql/
│   │   │   ├── client.ts           # GraphQL client setup
│   │   │   ├── queries.ts
│   │   │   ├── mutations.ts
│   │   │   └── subscriptions.ts
│   │   ├── hooks/
│   │   └── utils/
│   ├── package.json
│   └── Dockerfile
│
├── infrastructure/                  # Terraform IaC
│   ├── main.tf
│   ├── database.tf
│   ├── ecs.tf
│   ├── s3.tf
│   └── ...
│
├── docker-compose.yml              # Local development
└── README.md
```

---

## 🚀 STEG 1: Sett opp Backend (Uke 1)

### 1.1 Install Dependencies

```bash
# Create project
mkdir ai-erp && cd ai-erp
mkdir backend frontend infrastructure

cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install core packages
pip install fastapi[all] \
    strawberry-graphql[fastapi] \
    sqlalchemy[asyncio] \
    asyncpg \
    alembic \
    redis \
    celery \
    boto3 \
    anthropic \
    python-multipart \
    python-jose[cryptography] \
    passlib[bcrypt] \
    pydantic-settings

pip freeze > requirements.txt
```

### 1.2 Database Setup (SQLAlchemy Models)

**backend/app/database.py:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Async engine for PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency for GraphQL resolvers
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**backend/app/models/tenant.py:**
```python
from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base

class SubscriptionTier(str, enum.Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    org_number = Column(String(20), unique=True, nullable=False)
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.BASIC)
    max_clients = Column(Integer)
    billing_email = Column(String(255))
    settings = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clients = relationship("Client", back_populates="tenant")
    users = relationship("User", back_populates="tenant")
    
    def __repr__(self):
        return f"<Tenant {self.name}>"
```

**backend/app/models/client.py:**
```python
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base

class AutomationLevel(str, enum.Enum):
    FULL = "full"
    ASSISTED = "assisted"
    MANUAL = "manual"

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))
    client_number = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    org_number = Column(String(20), unique=True, nullable=False)
    
    # Integrations
    ehf_endpoint = Column(String(255))
    active_banks = Column(JSON)
    altinn_api_access = Column(Boolean, default=False)
    
    # Fiscal setup
    fiscal_year_start = Column(Integer, default=1)
    accounting_method = Column(String(20), default="accrual")
    vat_term = Column(String(20), default="bimonthly")
    base_currency = Column(String(3), default="NOK")
    
    # Agent settings
    ai_automation_level = Column(SQLEnum(AutomationLevel), default=AutomationLevel.ASSISTED)
    ai_confidence_threshold = Column(Integer, default=85)
    
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="clients")
    vendors = relationship("Vendor", back_populates="client")
    chart_of_accounts = relationship("Account", back_populates="client")
    
    def __repr__(self):
        return f"<Client {self.name}>"
```

**(Fortsett med andre models: vendor.py, general_ledger.py, etc. - følger samme mønster)**

### 1.3 FastAPI App Setup

**backend/app/main.py:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
import strawberry

from app.graphql.schema import schema
from app.config import settings

app = FastAPI(
    title="AI-Agent ERP",
    version="1.0.0",
    description="Agent-native ERP system"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GraphQL endpoint
graphql_app = GraphQLRouter(
    schema,
    graphiql=settings.DEBUG,  # GraphiQL UI in development
)
app.include_router(graphql_app, prefix="/graphql")

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Startup event
@app.on_event("startup")
async def startup():
    print("🚀 AI-Agent ERP started")
    # TODO: Initialize database connection pool
    # TODO: Connect to Redis
    # TODO: Start Celery workers

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

### 1.4 GraphQL Schema Setup

**backend/app/graphql/schema.py:**
```python
import strawberry
from typing import List
from app.graphql.types.client import Client
from app.graphql.types.vendor import Vendor
from app.graphql.queries.client import get_clients, get_client
from app.graphql.mutations.client import create_client

@strawberry.type
class Query:
    clients: List[Client] = strawberry.field(resolver=get_clients)
    client: Client = strawberry.field(resolver=get_client)

@strawberry.type
class Mutation:
    create_client: Client = strawberry.field(resolver=create_client)

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

**backend/app/graphql/types/client.py:**
```python
import strawberry
from typing import Optional, List
from datetime import datetime
import uuid

@strawberry.enum
class AutomationLevel:
    FULL = "full"
    ASSISTED = "assisted"
    MANUAL = "manual"

@strawberry.type
class Client:
    id: strawberry.ID
    tenant_id: strawberry.ID
    client_number: str
    name: str
    org_number: str
    base_currency: str
    ai_automation_level: AutomationLevel
    ai_confidence_threshold: int
    created_at: datetime
    
    # Computed fields
    @strawberry.field
    def total_invoices(self) -> int:
        # TODO: Query database for count
        return 0
    
    @strawberry.field
    def auto_booked_percentage(self) -> float:
        # TODO: Calculate from DB
        return 0.0
```

**backend/app/graphql/queries/client.py:**
```python
import strawberry
from typing import List, Optional
from app.graphql.types.client import Client
from app.database import get_db
from app.models.client import Client as ClientModel
from sqlalchemy import select

async def get_clients(
    tenant_id: Optional[strawberry.ID] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Client]:
    async with get_db() as db:
        query = select(ClientModel)
        
        if tenant_id:
            query = query.where(ClientModel.tenant_id == tenant_id)
        
        if search:
            query = query.where(ClientModel.name.ilike(f"%{search}%"))
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        clients = result.scalars().all()
        
        return [
            Client(
                id=str(c.id),
                tenant_id=str(c.tenant_id),
                client_number=c.client_number,
                name=c.name,
                org_number=c.org_number,
                base_currency=c.base_currency,
                ai_automation_level=c.ai_automation_level,
                ai_confidence_threshold=c.ai_confidence_threshold,
                created_at=c.created_at
            )
            for c in clients
        ]

async def get_client(id: strawberry.ID) -> Client:
    async with get_db() as db:
        result = await db.execute(
            select(ClientModel).where(ClientModel.id == id)
        )
        client = result.scalar_one_or_none()
        
        if not client:
            raise Exception(f"Client {id} not found")
        
        return Client(
            id=str(client.id),
            tenant_id=str(client.tenant_id),
            client_number=client.client_number,
            name=client.name,
            org_number=client.org_number,
            base_currency=client.base_currency,
            ai_automation_level=client.ai_automation_level,
            ai_confidence_threshold=client.ai_confidence_threshold,
            created_at=client.created_at
        )
```

---

## 🤖 STEG 2: Invoice Agent (Uke 2)

### 2.1 Claude API Integration

**backend/app/agents/invoice_agent.py:**
```python
import anthropic
import json
from typing import Dict, Any, Optional
from app.config import settings

class InvoiceAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"
    
    async def analyze_invoice(
        self,
        ocr_text: str,
        vendor_history: Optional[Dict] = None,
        learned_patterns: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze invoice and suggest booking
        
        Returns:
        {
            'vendor': {'name': '...', 'org_number': '...'},
            'invoice_number': '...',
            'invoice_date': '...',
            'due_date': '...',
            'amount_excl_vat': 1000.00,
            'vat_amount': 250.00,
            'total_amount': 1250.00,
            'currency': 'NOK',
            'line_items': [...],
            'suggested_booking': [
                {'account': '6300', 'debit': 1000, 'description': '...'},
                {'account': '2740', 'debit': 250, 'description': 'VAT'},
                {'account': '2400', 'credit': 1250, 'description': 'Vendor payable'}
            ],
            'confidence_score': 92,
            'reasoning': 'This invoice is from a known vendor...'
        }
        """
        
        # Build context with history and patterns
        context = self._build_context(vendor_history, learned_patterns)
        
        prompt = f"""You are an expert Norwegian accountant analyzing an invoice.

OCR Text from Invoice:
{ocr_text}

{context}

Please analyze this invoice and provide a JSON response with the following structure:
{{
    "vendor": {{
        "name": "Vendor name",
        "org_number": "Organization number if found"
    }},
    "invoice_number": "Invoice number",
    "invoice_date": "YYYY-MM-DD",
    "due_date": "YYYY-MM-DD",
    "amount_excl_vat": 0.00,
    "vat_amount": 0.00,
    "total_amount": 0.00,
    "currency": "NOK",
    "line_items": [
        {{"description": "...", "amount": 0.00, "vat_code": "5"}}
    ],
    "suggested_booking": [
        {{"account": "6300", "debit": 1000, "credit": 0, "description": "Office supplies"}},
        {{"account": "2740", "debit": 250, "credit": 0, "description": "Input VAT 25%"}},
        {{"account": "2400", "debit": 0, "credit": 1250, "description": "Accounts payable"}}
    ],
    "confidence_score": 0-100,
    "reasoning": "Brief explanation of your analysis and booking suggestion"
}}

Use Norwegian chart of accounts (NS 4102). Common expense accounts:
- 6000-6099: Inventory/materials
- 6100-6199: Services
- 6300-6399: Office expenses
- 6500-6599: Travel
- 6700-6799: Marketing
- 2400-2499: Accounts payable
- 2700-2799: VAT accounts

Only return the JSON object, no other text."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse response
        response_text = message.content[0].text
        
        try:
            result = json.loads(response_text)
            
            # Adjust confidence based on patterns
            if learned_patterns:
                result['confidence_score'] = self._adjust_confidence(
                    result,
                    learned_patterns
                )
            
            return result
            
        except json.JSONDecodeError:
            # Fallback if AI didn't return valid JSON
            return {
                'error': 'Failed to parse invoice',
                'confidence_score': 0,
                'reasoning': 'Could not extract structured data from invoice'
            }
    
    def _build_context(
        self,
        vendor_history: Optional[Dict],
        learned_patterns: Optional[Dict]
    ) -> str:
        context = ""
        
        if vendor_history:
            context += f"""
Previous invoices from this vendor:
{json.dumps(vendor_history, indent=2)}
"""
        
        if learned_patterns:
            context += f"""
Learned patterns for similar invoices:
{json.dumps(learned_patterns, indent=2)}
"""
        
        return context
    
    def _adjust_confidence(
        self,
        result: Dict,
        patterns: Dict
    ) -> int:
        base_confidence = result.get('confidence_score', 50)
        
        # Boost confidence if matches known pattern
        if patterns.get('success_rate', 0) > 0.90:
            base_confidence = min(100, base_confidence + 15)
        
        return base_confidence
```

### 2.2 OCR Service (AWS Textract)

**backend/app/services/ocr_service.py:**
```python
import boto3
from typing import Dict
from app.config import settings

class OCRService:
    def __init__(self):
        self.textract = boto3.client(
            'textract',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY
        )
    
    async def extract_text_from_pdf(self, s3_bucket: str, s3_key: str) -> str:
        """
        Extract text from PDF stored in S3 using AWS Textract
        """
        response = self.textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': s3_key
                }
            }
        )
        
        # Combine all text blocks
        text = ""
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                text += block['Text'] + "\n"
        
        return text
    
    async def extract_structured_data(self, s3_bucket: str, s3_key: str) -> Dict:
        """
        Extract structured data (tables, key-value pairs) from PDF
        """
        response = self.textract.analyze_document(
            Document={
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': s3_key
                }
            },
            FeatureTypes=['TABLES', 'FORMS']
        )
        
        # Parse tables and forms
        # TODO: Implement table/form parsing
        
        return response
```

### 2.3 Invoice Processing Task (Celery)

**backend/app/tasks/invoice_processing.py:**
```python
from celery import shared_task
from app.agents.invoice_agent import InvoiceAgent
from app.agents.orchestrator import OrchestratorAgent
from app.services.ocr_service import OCRService
from app.models.vendor_invoice import VendorInvoice
from app.database import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_invoice(invoice_id: str):
    """
    Background task to process uploaded invoice
    """
    asyncio.run(_process_invoice_async(invoice_id))

async def _process_invoice_async(invoice_id: str):
    async with AsyncSessionLocal() as db:
        # Get invoice
        invoice = await db.get(VendorInvoice, invoice_id)
        if not invoice:
            logger.error(f"Invoice {invoice_id} not found")
            return
        
        try:
            # Step 1: OCR
            logger.info(f"Starting OCR for invoice {invoice_id}")
            ocr_service = OCRService()
            ocr_text = await ocr_service.extract_text_from_pdf(
                invoice.document.s3_bucket,
                invoice.document.s3_key
            )
            
            # Step 2: Get vendor history and learned patterns
            vendor_history = await _get_vendor_history(db, invoice.vendor_id)
            learned_patterns = await _get_learned_patterns(db, invoice.client_id)
            
            # Step 3: AI Analysis
            logger.info(f"Analyzing invoice {invoice_id} with AI")
            invoice_agent = InvoiceAgent()
            analysis = await invoice_agent.analyze_invoice(
                ocr_text,
                vendor_history,
                learned_patterns
            )
            
            # Step 4: Orchestrator decides
            orchestrator = OrchestratorAgent()
            decision = await orchestrator.decide_invoice_action(
                invoice,
                analysis
            )
            
            # Step 5: Execute decision
            if decision['action'] == 'auto_book':
                await _auto_book_invoice(db, invoice, analysis)
            else:
                await _send_to_review_queue(db, invoice, analysis, decision['reason'])
            
            logger.info(f"Invoice {invoice_id} processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing invoice {invoice_id}: {str(e)}")
            invoice.review_status = "needs_review"
            invoice.ai_detected_issues = [str(e)]
            await db.commit()

async def _auto_book_invoice(db, invoice, analysis):
    # Create GL entry from analysis
    # TODO: Implement GL entry creation
    pass

async def _send_to_review_queue(db, invoice, analysis, reason):
    # Create review queue item
    # TODO: Implement review queue creation
    pass
```

---

## 🎨 STEG 3: Frontend Dashboard (Uke 3)

### 3.1 Setup React + TypeScript

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install

# Install dependencies
npm install @apollo/client graphql \
    @tanstack/react-query \
    react-router-dom \
    @hookform/resolvers zod react-hook-form \
    recharts \
    lucide-react \
    clsx tailwind-merge \
    date-fns

# shadcn/ui setup
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card table dialog form input
```

### 3.2 GraphQL Client Setup

**frontend/src/graphql/client.ts:**
```typescript
import { ApolloClient, InMemoryCache, HttpLink, split } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { getMainDefinition } from '@apollo/client/utilities';
import { createClient } from 'graphql-ws';

const httpLink = new HttpLink({
  uri: 'http://localhost:8000/graphql',
  credentials: 'include',
});

const wsLink = new GraphQLWsLink(
  createClient({
    url: 'ws://localhost:8000/graphql/ws',
  })
);

// Split for subscriptions
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink
);

export const apolloClient = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache(),
});
```

### 3.3 Review Queue Component

**frontend/src/components/ReviewQueue.tsx:**
```typescript
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const GET_REVIEW_QUEUE = gql`
  query GetReviewQueue($clientId: ID!) {
    reviewQueue(clientId: $clientId, status: PENDING, limit: 20) {
      id
      priority
      issueCategory
      issueDescription
      vendorInvoice {
        invoiceNumber
        invoiceDate
        totalAmount
        currency
        vendor {
          name
        }
        document {
          downloadUrl
        }
      }
      aiSuggestion
      aiConfidence
      aiReasoning
    }
  }
`;

const APPROVE_REVIEW = gql`
  mutation ApproveReview($reviewId: ID!) {
    approveReview(reviewId: $reviewId) {
      id
      status
    }
  }
`;

export function ReviewQueue({ clientId }: { clientId: string }) {
  const { data, loading } = useQuery(GET_REVIEW_QUEUE, {
    variables: { clientId },
    pollInterval: 5000, // Refresh every 5s
  });

  const [approveReview] = useMutation(APPROVE_REVIEW, {
    refetchQueries: ['GetReviewQueue'],
  });

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Review Queue</h2>
      
      {data?.reviewQueue.map((item: any) => (
        <Card key={item.id} className="p-4">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex gap-2 items-center mb-2">
                <Badge variant={
                  item.priority === 'HIGH' ? 'destructive' : 'default'
                }>
                  {item.priority}
                </Badge>
                <Badge variant="outline">{item.issueCategory}</Badge>
              </div>
              
              <h3 className="font-semibold">
                {item.vendorInvoice?.vendor?.name}
              </h3>
              <p className="text-sm text-muted-foreground">
                Invoice: {item.vendorInvoice?.invoiceNumber} • 
                {item.vendorInvoice?.totalAmount} {item.vendorInvoice?.currency}
              </p>
              
              <p className="mt-2 text-sm">{item.issueDescription}</p>
              
              <div className="mt-3 p-3 bg-blue-50 rounded">
                <p className="text-sm font-medium">AI Suggestion (Confidence: {item.aiConfidence}%)</p>
                <pre className="text-xs mt-1">
                  {JSON.stringify(item.aiSuggestion, null, 2)}
                </pre>
                <p className="text-xs mt-2 italic">{item.aiReasoning}</p>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button
                onClick={() => approveReview({ variables: { reviewId: item.id } })}
                size="sm"
              >
                Approve
              </Button>
              <Button variant="outline" size="sm">
                Edit
              </Button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
```

---

## 🚀 STEG 4: Deployment (Uke 4)

### 4.1 Docker Setup

**backend/Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml (Local Development):**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ai_erp
      POSTGRES_USER: erp_user
      POSTGRES_PASSWORD: erp_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://erp_user:erp_password@postgres:5432/ai_erp
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
```

### 4.2 AWS Deployment (Terraform)

**infrastructure/main.tf:**
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-north-1"  # Stockholm/Oslo
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "ai-erp-vpc"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier        = "ai-erp-db"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.medium"  # Start small
  allocated_storage = 100
  
  db_name  = "ai_erp"
  username = "erp_admin"
  password = var.db_password
  
  multi_az               = true
  backup_retention_period = 7
  skip_final_snapshot    = false
  
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  tags = {
    Name = "ai-erp-database"
  }
}

# S3 Bucket for documents
resource "aws_s3_bucket" "documents" {
  bucket = "ai-erp-documents-prod"
  
  tags = {
    Name = "AI ERP Documents"
  }
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "ai-erp-cluster"
}

# ... (mer Terraform config)
```

---

## 📋 NEXT STEPS CHECKLIST

### Week 1: Backend Foundation
- [ ] Set up PostgreSQL database (local + AWS RDS)
- [ ] Create all SQLAlchemy models
- [ ] Set up Alembic migrations
- [ ] Implement FastAPI + GraphQL API
- [ ] Write basic queries (clients, vendors)
- [ ] Set up authentication (JWT)

### Week 2: Agent Development
- [ ] Integrate Claude API
- [ ] Build Invoice Agent
- [ ] Set up AWS Textract OCR
- [ ] Implement Celery task queue
- [ ] Test invoice processing pipeline
- [ ] Add agent decision logging

### Week 3: Frontend Dashboard
- [ ] Set up React + TypeScript
- [ ] Implement GraphQL client
- [ ] Build Review Queue component
- [ ] Build Invoice Viewer with PDF display
- [ ] Add real-time updates (subscriptions)
- [ ] Implement "Apply to Similar" feature

### Week 4: Testing & Deployment
- [ ] Write unit tests (pytest)
- [ ] Integration tests
- [ ] Set up CI/CD (GitHub Actions)
- [ ] Deploy to AWS (Terraform)
- [ ] Load testing (1000 invoices)
- [ ] Security audit

---

## 🎯 FØRSTE PILOT (Måned 2)

**Mål:** 1 regnskapsbyrå, 10 klienter, 2000 fakturaer/måned

**Suksesskriterier:**
- 70%+ auto-booking rate
- < 5 sekunder processing tid per faktura
- 90%+ accountant satisfaction
- 0 data loss
- < 2% error rate

**Start med pilot ASAP når backend er klar!** 🚀
