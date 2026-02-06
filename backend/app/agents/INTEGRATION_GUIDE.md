# Integration Guide - Multi-Agent System

Denne guiden viser hvordan du integrerer multi-agent systemet med eksisterende FastAPI backend.

---

## 1. Database Migrations

### Opprett Alembic migration

```bash
cd backend
alembic revision --autogenerate -m "Add multi-agent system tables"
```

Dette vil opprette migration for:
- `agent_tasks`
- `agent_events`
- `corrections`

### Kjør migration

```bash
alembic upgrade head
```

### Verifiser tabeller

```sql
\dt agent_*
\dt corrections
```

Skal vise:
- agent_decisions (eksisterende)
- agent_events (ny)
- agent_learned_patterns (eksisterende)
- agent_tasks (ny)
- corrections (ny)

---

## 2. FastAPI Integration

### A. Event Publishing fra API

Når du mottar en EHF-faktura via API, publish event:

**backend/app/api/webhooks/ehf.py:**

```python
from app.models.agent_event import AgentEvent
from app.database import get_db

@router.post("/ehf/receive")
async def receive_ehf_invoice(
    file: UploadFile,
    db: AsyncSession = Depends(get_db)
):
    # Parse EHF (eksisterende kode)
    # ...
    
    # Opprett invoice record
    invoice = VendorInvoice(
        client_id=client_id,
        ehf_raw_xml=xml_content,
        review_status="received"
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    # 🆕 PUBLISH EVENT for agent system
    event = AgentEvent(
        tenant_id=client_id,
        event_type="invoice_received",
        payload={"invoice_id": str(invoice.id)}
    )
    db.add(event)
    await db.commit()
    
    return {"message": "Invoice received", "invoice_id": str(invoice.id)}
```

### B. Correction API Endpoint

Når regnskapsfører korrigerer en bokføring:

**backend/app/api/v1/review_queue.py (ny fil):**

```python
from fastapi import APIRouter, Depends
from app.models.correction import Correction
from app.models.agent_event import AgentEvent
from app.database import get_db

router = APIRouter(prefix="/api/v1/review-queue", tags=["Review Queue"])

@router.post("/{review_id}/correct")
async def correct_booking(
    review_id: str,
    correction_data: CorrectionRequest,
    db: AsyncSession = Depends(get_db)
):
    # Get review item
    review = await db.get(ReviewQueue, review_id)
    
    # Create correction record
    correction = Correction(
        tenant_id=review.client_id,
        review_queue_id=review.id,
        journal_entry_id=correction_data.journal_entry_id,
        original_entry=correction_data.original,
        corrected_entry=correction_data.corrected,
        correction_reason=correction_data.reason,
        corrected_by=current_user.id  # from auth
    )
    db.add(correction)
    await db.commit()
    
    # Reverse original entry (create reversal)
    reversal = await create_reversal_entry(
        db, 
        correction_data.journal_entry_id
    )
    
    # Create new correct entry
    new_entry = await create_journal_entry(
        db,
        correction_data.corrected
    )
    
    # 🆕 PUBLISH EVENT for learning agent
    event = AgentEvent(
        tenant_id=review.client_id,
        event_type="correction_received",
        payload={"correction_id": str(correction.id)}
    )
    db.add(event)
    await db.commit()
    
    return {
        "correction_id": str(correction.id),
        "reversal_id": str(reversal.id),
        "new_entry_id": str(new_entry.id)
    }
```

### C. Add to main.py

**backend/app/main.py:**

```python
from fastapi import FastAPI
from app.api.v1 import review_queue  # new

app = FastAPI(title="Kontali ERP")

# Existing routes
app.include_router(...)

# 🆕 Add review queue routes
app.include_router(review_queue.router)
```

---

## 3. Start Agent Services

### Development (manual)

```bash
# Terminal 1
python -m app.agents.run_orchestrator

# Terminal 2  
python -m app.agents.worker invoice_parser

# Terminal 3
python -m app.agents.worker bookkeeper

# Terminal 4 (optional)
python -m app.agents.worker learning
```

### Production (Systemd)

**Opprett service files:**

**/etc/systemd/system/kontali-orchestrator.service:**

```ini
[Unit]
Description=Kontali ERP Orchestrator Agent
After=network.target postgresql.service

[Service]
Type=simple
User=kontali
WorkingDirectory=/opt/kontali/backend
Environment="PATH=/opt/kontali/backend/venv/bin"
ExecStart=/opt/kontali/backend/venv/bin/python -m app.agents.run_orchestrator
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**/etc/systemd/system/kontali-worker-parser.service:**

```ini
[Unit]
Description=Kontali ERP Invoice Parser Worker
After=network.target postgresql.service

[Service]
Type=simple
User=kontali
WorkingDirectory=/opt/kontali/backend
Environment="PATH=/opt/kontali/backend/venv/bin"
ExecStart=/opt/kontali/backend/venv/bin/python -m app.agents.worker invoice_parser
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**/etc/systemd/system/kontali-worker-bookkeeper.service:**

```ini
[Unit]
Description=Kontali ERP Bookkeeping Worker
After=network.target postgresql.service

[Service]
Type=simple
User=kontali
WorkingDirectory=/opt/kontali/backend
Environment="PATH=/opt/kontali/backend/venv/bin"
ExecStart=/opt/kontali/backend/venv/bin/python -m app.agents.worker bookkeeper
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable og start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable kontali-orchestrator
sudo systemctl enable kontali-worker-parser
sudo systemctl enable kontali-worker-bookkeeper

sudo systemctl start kontali-orchestrator
sudo systemctl start kontali-worker-parser
sudo systemctl start kontali-worker-bookkeeper
```

**Check status:**

```bash
sudo systemctl status kontali-orchestrator
sudo systemctl status kontali-worker-parser
sudo systemctl status kontali-worker-bookkeeper
```

---

## 4. Frontend Integration

### Review Queue Component

Frontend må hente data fra `/api/v1/review-queue`:

```typescript
// ReviewQueueList.tsx
interface ReviewItem {
  id: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  issue_category: string;
  ai_confidence: number;
  ai_reasoning: string;
  invoice: {...};
  journal_entry: {...};
}

const ReviewQueue = () => {
  const { data: items } = useQuery<ReviewItem[]>({
    queryKey: ['review-queue'],
    queryFn: () => 
      fetch('/api/v1/review-queue?status=pending')
        .then(r => r.json())
  });
  
  return (
    <div>
      {items?.map(item => (
        <ReviewCard 
          key={item.id} 
          item={item}
          onApprove={() => approveBooking(item.id)}
          onCorrect={(data) => correctBooking(item.id, data)}
        />
      ))}
    </div>
  );
};
```

### Approve/Correct Actions

```typescript
const approveBooking = async (reviewId: string) => {
  await fetch(`/api/v1/review-queue/${reviewId}/approve`, {
    method: 'POST'
  });
};

const correctBooking = async (reviewId: string, correctionData: any) => {
  await fetch(`/api/v1/review-queue/${reviewId}/correct`, {
    method: 'POST',
    body: JSON.stringify(correctionData)
  });
};
```

---

## 5. Monitoring

### Health Check Endpoint

**backend/app/api/v1/health.py:**

```python
from fastapi import APIRouter, Depends
from app.database import get_db
from app.models.agent_event import AgentEvent
from app.models.agent_task import AgentTask

router = APIRouter(prefix="/api/v1/health", tags=["Health"])

@router.get("/agents")
async def agent_health(db: AsyncSession = Depends(get_db)):
    # Check unprocessed events
    result = await db.execute(
        select(func.count(AgentEvent.id))
        .where(AgentEvent.processed == False)
    )
    unprocessed_events = result.scalar()
    
    # Check failed tasks
    result = await db.execute(
        select(func.count(AgentTask.id))
        .where(AgentTask.status == 'failed')
    )
    failed_tasks = result.scalar()
    
    # Health status
    status = "healthy"
    if unprocessed_events > 100:
        status = "degraded"  # Orchestrator might be slow
    if failed_tasks > 10:
        status = "unhealthy"  # Many failures
    
    return {
        "status": status,
        "unprocessed_events": unprocessed_events,
        "failed_tasks": failed_tasks
    }
```

### Prometheus Metrics (optional)

```python
from prometheus_client import Counter, Gauge

events_processed = Counter(
    'agent_events_processed_total',
    'Total events processed by orchestrator'
)

tasks_completed = Counter(
    'agent_tasks_completed_total',
    'Total tasks completed',
    ['agent_type']
)

review_queue_size = Gauge(
    'review_queue_pending',
    'Number of pending review items'
)
```

---

## 6. Testing Full Flow

### Manual Test

```bash
# 1. Get a client ID
psql kontali -c "SELECT id FROM clients LIMIT 1;"

# 2. Trigger test flow
python -m app.agents.utils trigger <client-id>

# 3. Watch logs
tail -f orchestrator.log parser.log bookkeeper.log

# 4. Check review queue
psql kontali -c "SELECT * FROM review_queue WHERE status='pending';"
```

### Automated Test Script

**backend/scripts/test_agent_flow.py:**

```python
import asyncio
from app.agents.utils import trigger_test_flow
from app.database import get_db

async def main():
    client_id = "..." # your test client
    
    async with get_db() as db:
        print("Starting test flow...")
        await trigger_test_flow(db, client_id)
        print("Done! Check logs and database.")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 7. Troubleshooting

### Events not processed

**Check:**
```bash
# Is orchestrator running?
ps aux | grep orchestrator

# Any errors in logs?
tail -n 100 orchestrator.log

# Unprocessed events stuck?
psql kontali -c "SELECT * FROM agent_events WHERE processed=false ORDER BY created_at;"
```

**Fix:**
```bash
# Restart orchestrator
sudo systemctl restart kontali-orchestrator
```

### Tasks stuck in pending

**Check:**
```bash
# Are workers running?
ps aux | grep "agents.worker"

# Pending tasks?
psql kontali -c "SELECT agent_type, COUNT(*) FROM agent_tasks WHERE status='pending' GROUP BY agent_type;"
```

**Fix:**
```bash
# Start missing worker
sudo systemctl start kontali-worker-bookkeeper
```

### High error rate

**Check failed tasks:**
```sql
SELECT 
    task_type,
    error_message,
    COUNT(*)
FROM agent_tasks 
WHERE status = 'failed'
GROUP BY task_type, error_message
ORDER BY COUNT(*) DESC;
```

**Common errors:**
- `Claude API not configured` → Set ANTHROPIC_API_KEY
- `Invoice not found` → Database sync issue
- `Unbalanced entry` → AI logic needs tuning

---

## 8. Rollout Plan

### Phase 1: Testing (1 uke)

1. ✅ Setup agents på staging
2. ✅ Import test invoices
3. ✅ Run through full flow
4. ✅ Review AI suggestions
5. ✅ Adjust confidence thresholds

### Phase 2: Pilot (2-4 uker)

1. ✅ Select 1-2 pilot clients
2. ✅ Enable agent system for pilot
3. ✅ Monitor daily
4. ✅ Collect feedback
5. ✅ Make corrections → learn patterns

### Phase 3: Gradual Rollout

1. ✅ 10 clients
2. ✅ Monitor patterns learned
3. ✅ Adjust thresholds per client type
4. ✅ Full rollout

---

## 9. Backup & Recovery

### Backup Critical Tables

```bash
# Backup patterns (valuable learning data)
pg_dump kontali -t agent_learned_patterns > patterns_backup.sql

# Backup corrections (audit trail)
pg_dump kontali -t corrections > corrections_backup.sql
```

### Recovery from Failed Tasks

```sql
-- Reset failed tasks to retry
UPDATE agent_tasks 
SET status = 'pending', retry_count = 0, error_message = NULL
WHERE status = 'failed' AND created_at > NOW() - INTERVAL '1 hour';
```

---

**Integration ferdig!** 🚀

Systemet er nå koblet til eksisterende FastAPI backend og klar for testing.
