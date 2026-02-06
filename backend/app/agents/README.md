# Multi-Agent System - Kontali ERP

Dette er implementeringen av multi-agent-systemet for Kontali ERP, basert på ARCHITECTURE.md.

## Arkitektur

```
┌──────────────────────────────────────────────────────────┐
│                   REGNSKAPSFØRER                          │
│                 (Review Queue UI)                         │
└──────────────┬───────────────────────┬──────────────────┘
               │ Godkjenn/Korriger     │ Chat
               ▼                       ▼
┌──────────────────────────────────────────────────────────┐
│                  ORKESTRATOR-AGENT                        │
│  • Mottar hendelser (agent_events)                        │
│  • Oppretter oppgaver (agent_tasks)                       │
│  • Evaluerer confidence → review queue                    │
└────┬──────────────┬──────────────┬──────────────────────┘
     │              │              │
     ▼              ▼              ▼
┌─────────┐  ┌───────────┐  ┌──────────┐
│ FAKTURA │  │ BOKFØRINGS │  │ LEARNING │
│ PARSER  │  │ AGENT      │  │ AGENT    │
└─────────┘  └───────────┘  └──────────┘
```

## Agenter

### 1. Orkestrator (orchestrator.py)

**Ansvar:**
- Poller `agent_events` tabell hvert 30. sekund
- MATCH på `event_type` → oppretter `agent_task`
- Evaluerer confidence scores
- Sender til review queue eller auto-godkjenner

**Kjøre:**
```bash
python -m app.agents.run_orchestrator
```

### 2. Invoice Parser Agent (invoice_parser_agent.py)

**Ansvar:**
- Parser EHF XML til strukturert data
- Matcher/oppretter leverandør
- Populerer `invoices` tabell
- Emit event: 'invoice_parsed'

**Kjøre:**
```bash
python -m app.agents.worker invoice_parser
```

### 3. Bookkeeping Agent (bookkeeping_agent.py)

**Ansvar:**
- Leser parsed faktura
- Query `patterns` tabell for lærte regler
- Velger konti (debit/credit)
- Beregner MVA
- Genererer `ai_reasoning`
- Beregner `confidence_score`
- Opprett `journal_entry`
- Emit event: 'booking_completed'

**Kjøre:**
```bash
python -m app.agents.worker bookkeeper
```

### 4. Learning Agent (learning_agent.py)

**Ansvar:**
- Prosesserer korreksjoner fra regnskapsfører
- Oppretter/oppdaterer mønstre
- Finner lignende feil
- Systemet blir bedre over tid!

**Kjøre:**
```bash
python -m app.agents.worker learning
```

## Kommunikasjon

**VIKTIG:** Agenter snakker ALDRI direkte med hverandre!

All kommunikasjon skjer via databasen:

1. **Event Publishing:**
   ```python
   await agent.publish_event(
       db,
       tenant_id="...",
       event_type="invoice_parsed",
       payload={"invoice_id": "..."}
   )
   ```

2. **Orkestrator fanger event:**
   ```python
   events = await fetch_unprocessed_events(db)
   for event in events:
       await handle_event(db, event)
   ```

3. **Orkestrator oppretter task:**
   ```python
   task = AgentTask(
       agent_type="bookkeeper",
       task_type="book_invoice",
       payload={"invoice_id": "..."}
   )
   db.add(task)
   ```

4. **Agent claimer task:**
   ```python
   task = await agent.claim_next_task(db)
   result = await agent.execute_task(db, task)
   await agent.complete_task(db, task.id, result)
   ```

## Event Types

| Event Type | Trigges av | Leder til |
|------------|-----------|-----------|
| `invoice_received` | System (EHF mottak) | Parse task |
| `invoice_parsed` | Invoice Parser | Booking task |
| `booking_completed` | Bookkeeping Agent | Auto-approve eller review |
| `correction_received` | Frontend API | Learning task |

## Task Types

| Task Type | Agent | Input | Output |
|-----------|-------|-------|--------|
| `parse_invoice` | invoice_parser | invoice_id | Parsed data |
| `book_invoice` | bookkeeper | invoice_id | journal_entry_id |
| `process_correction` | learning | correction_id | pattern_id |

## Kjøre hele systemet

### Development (manual)

Start hver agent i eget terminal:

```bash
# Terminal 1: Orkestrator
python -m app.agents.run_orchestrator

# Terminal 2: Invoice Parser
python -m app.agents.worker invoice_parser

# Terminal 3: Bookkeeper
python -m app.agents.worker bookkeeper

# Terminal 4: Learning
python -m app.agents.worker learning
```

### Production (systemd/supervisor)

Se `infrastructure/` for deployment configs.

## Testing

### Unit tests (mocked - ingen database)

```bash
pytest tests/test_agents.py -v
```

### Integration tests (krever database)

```bash
# Først: run migrations
alembic upgrade head

# Kjør integration tests
pytest tests/test_agents.py -v -m integration
```

## Debugging

### Se agent events

```sql
SELECT * FROM agent_events 
WHERE processed = false 
ORDER BY created_at DESC;
```

### Se agent tasks

```sql
SELECT * FROM agent_tasks 
WHERE status = 'pending' 
ORDER BY priority DESC, created_at ASC;
```

### Se review queue

```sql
SELECT * FROM review_queue 
WHERE status = 'pending' 
ORDER BY priority, created_at;
```

### Se audit log

```sql
SELECT * FROM audit_log 
WHERE actor_type = 'ai' 
ORDER BY created_at DESC 
LIMIT 50;
```

## Trigger manuelt event (testing)

```python
from app.models.agent_event import AgentEvent
from app.database import get_db

# Trigger invoice parsing
event = AgentEvent(
    tenant_id="<client-uuid>",
    event_type="invoice_received",
    payload={"invoice_id": "<invoice-uuid>"}
)

async with get_db() as db:
    db.add(event)
    await db.commit()
```

Orkestratoren vil plukke opp eventet innen 30 sekunder.

## Confidence Thresholds

Kan konfigureres per tenant (hardkodet i MVP):

| Confidence | Action |
|------------|--------|
| 85-99% | Auto-godkjenn |
| 60-84% | Review queue (medium prioritet) |
| 40-59% | Review queue (høy prioritet) |
| 0-39% | Review queue (kritisk prioritet) |

## Logging

Alle agenter logger til standard Python logging:

```python
import logging
logger = logging.getLogger(__name__)
```

Konfigurer logging level:

```bash
# I .env
LOG_LEVEL=INFO
```

## Performance

**Estimert gjennomstrømning (med Claude Sonnet):**

- Invoice Parser: ~100 fakturaer/time
- Bookkeeping Agent: ~50 bokføringer/time (avhenger av Claude API)
- Learning Agent: ~200 korreksjoner/time

**Skalering:**

Kjør flere workers av samme type:

```bash
# Start 3 bookkeeper workers
python -m app.agents.worker bookkeeper &
python -m app.agents.worker bookkeeper &
python -m app.agents.worker bookkeeper &
```

Tasks claimes atomisk med `FOR UPDATE SKIP LOCKED`, så ingen race conditions.

## Feilhåndtering

Agenter har automatisk retry:

- Max 3 retries per task (konfigurerbar)
- Exponential backoff (implisitt via polling)
- Failed tasks logges i `agent_tasks.error_message`

## Neste steg

1. ✅ Database migrations
2. ✅ Grunnleggende agenter
3. ⏳ Avstemming-agent (fase 2)
4. ⏳ Rapport-agent (fase 2)
5. ⏳ Multi-tenant pattern deling (fase 3)
