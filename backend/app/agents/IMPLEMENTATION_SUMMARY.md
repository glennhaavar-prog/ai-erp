# Multi-Agent System - Implementation Summary

## ✅ Completed (12-16 timer arbeid)

Dette dokumentet oppsummerer det komplette multi-agent systemet som er bygget for Kontali ERP.

---

## 📦 Hva er bygget

### 1. Database Models (3 nye modeller)

**✅ agent_task.py**
- Oppgaver for agenter
- Status tracking (pending/in_progress/completed/failed)
- Prioritet (1-10)
- Retry logic (max 3 retries)
- Parent-child task relationships

**✅ agent_event.py**
- Hendelser som trigger orkestratoren
- Event types: invoice_received, invoice_parsed, booking_completed, correction_received
- Processed flag for å unngå duplikat-prosessering

**✅ correction.py**
- Lagrer menneskelige korreksjoner
- Original vs corrected entry
- Correction reason (naturlig språk)
- Batch correction support
- Koblet til patterns for læring

### 2. Agent Classes (5 agenter)

**✅ base.py - BaseAgent**
- Felles funksjonalitet for alle agenter
- Task claiming (atomisk med FOR UPDATE SKIP LOCKED)
- Event publishing
- Audit logging
- Claude API wrapper

**✅ orchestrator.py - OrchestratorAgent**
- Event loop (poller hver 30. sekund)
- Event handling for alle event types
- Confidence evaluation
- Auto-approve vs review queue routing
- Priority assignment

**✅ invoice_parser_agent.py - InvoiceParserAgent**
- Parser EHF XML (integrasjon med eksisterende parser)
- Find/create vendor
- Populate invoices tabell
- Emit invoice_parsed event
- Error handling og logging

**✅ bookkeeping_agent.py - BookkeepingAgent**
- Les parsed faktura
- Query patterns tabell for lærte regler
- Claude API for booking suggestion
- Pattern confidence boost
- Balance validation
- Fallback booking for errors
- Create journal entry med lines
- Emit booking_completed event

**✅ learning_agent.py - LearningAgent**
- Prosesser corrections
- Analyze correction → pattern type
- Create/update learned patterns
- Find similar entries for batch correction
- Pattern success rate tracking

### 3. Runner Scripts

**✅ run_orchestrator.py**
- Starter orkestrator event loop
- Async database connection
- Graceful shutdown (CTRL+C)

**✅ worker.py - AgentWorker**
- Generic worker for alle agent-typer
- Claim → Execute → Complete loop
- Error handling med retry
- Configurable polling interval

### 4. Utilities & Testing

**✅ utils.py**
- Manual event triggering for testing
- Create test invoice
- Full flow trigger
- Agent statistics
- CLI interface

**✅ test_agents.py**
- Unit tests med mocks (no database required)
- Test orchestrator event handling
- Test bookkeeping agent logic
- Test learning agent keyword extraction
- Integration test placeholders

**✅ README.md**
- Komplett dokumentasjon
- Arkitektur diagram
- Agent beskrivelser
- Kjøreinstruksjoner
- Debugging guide
- Performance notes

**✅ __init__.py**
- Module exports
- Usage examples

---

## 🎯 Arkitektur-detaljer

### Kommunikasjon (Database-Only)

```
Event Publishing:
┌──────────┐
│  Agent   │ → INSERT INTO agent_events
└──────────┘

Orchestrator:
┌──────────┐
│Orchestr. │ → SELECT * FROM agent_events WHERE processed=false
└──────────┘    → INSERT INTO agent_tasks
                → UPDATE agent_events SET processed=true

Agent Workers:
┌──────────┐
│  Agent   │ → UPDATE agent_tasks SET status='in_progress' 
└──────────┘    WHERE id=... FOR UPDATE SKIP LOCKED
                → Execute task
                → UPDATE agent_tasks SET status='completed'
                → INSERT INTO agent_events (next event)
```

### Confidence Flow

```
Bookkeeping Agent:
├─ Base confidence (från Claude): 50-95%
├─ Pattern boost: +15% (if high-success pattern)
├─ Validation: -50% (if unbalanced)
└─ Final confidence: 0-99%

Orchestrator:
├─ >= 85% → Auto-approve (status='posted')
├─ 60-84% → Review queue (priority=medium)
├─ 40-59% → Review queue (priority=high)
└─ < 40%  → Review queue (priority=critical)
```

### Learning Mechanism

```
Correction received:
├─ Analyze correction
│  ├─ Vendor-based? → vendor_account pattern
│  └─ Keyword-based? → description_keyword pattern
│
├─ Find/create pattern
│  ├─ Existing pattern? → Update success_rate
│  └─ New pattern? → Create with 100% success_rate
│
└─ Find similar entries
   └─ Suggest batch correction (future)
```

---

## 🚀 Hvordan kjøre

### 1. Database Setup

**Først: Kjør migrations for nye modeller**

Du må lage Alembic migration for de tre nye modellene:
- agent_task
- agent_event  
- correction

Eller kjør migrations som allerede finnes (hvis du har laget dem).

```bash
cd backend
alembic revision --autogenerate -m "Add agent system tables"
alembic upgrade head
```

### 2. Start Agentene

**Terminal 1 - Orchestrator:**
```bash
cd backend
python -m app.agents.run_orchestrator
```

**Terminal 2 - Invoice Parser:**
```bash
python -m app.agents.worker invoice_parser
```

**Terminal 3 - Bookkeeper:**
```bash
python -m app.agents.worker bookkeeper
```

**Terminal 4 - Learning (optional):**
```bash
python -m app.agents.worker learning
```

### 3. Test systemet

**Manuell trigger:**
```bash
# Hent en client_id från database
python -m app.agents.utils trigger <client-uuid>
```

Dette vil:
1. Opprette test-faktura med EHF XML
2. Trigge invoice_received event
3. Se hele flyten i loggene

**Se statistikk:**
```bash
python -m app.agents.utils stats <client-uuid>
```

---

## 🧪 Testing

### Unit tests (no database)

```bash
cd backend
pytest tests/test_agents.py -v
```

Disse testene bruker mocks og krever IKKE database.

### Integration tests (med database)

```bash
# Krever migrations + ANTHROPIC_API_KEY
pytest tests/test_agents.py -v -m integration
```

---

## 📊 Monitoring & Debugging

### Se ubehandlede events

```sql
SELECT 
    id, 
    event_type, 
    created_at,
    payload
FROM agent_events 
WHERE processed = false 
ORDER BY created_at DESC;
```

### Se pending tasks

```sql
SELECT 
    id,
    agent_type,
    task_type,
    priority,
    created_at,
    retry_count
FROM agent_tasks 
WHERE status = 'pending' 
ORDER BY priority DESC, created_at ASC;
```

### Se review queue

```sql
SELECT 
    id,
    priority,
    issue_category,
    ai_confidence,
    created_at
FROM review_queue 
WHERE status = 'pending' 
ORDER BY 
    CASE priority 
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END,
    created_at;
```

### Se learned patterns

```sql
SELECT 
    pattern_type,
    pattern_name,
    success_rate,
    times_applied,
    is_active
FROM agent_learned_patterns
WHERE is_active = true
ORDER BY success_rate DESC;
```

### Se audit trail

```sql
SELECT 
    action,
    entity_type,
    entity_id,
    actor_type,
    actor_id,
    created_at
FROM audit_log
WHERE actor_type = 'ai'
ORDER BY created_at DESC
LIMIT 100;
```

---

## 🔧 Konfigurasjon

### Environment Variables

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096

DATABASE_URL=postgresql+asyncpg://user:pass@localhost/kontali

LOG_LEVEL=INFO
```

### Confidence Thresholds (hardkodet i MVP)

Kan endres i `orchestrator.py`:

```python
AUTO_APPROVE_THRESHOLD = 85  # Kan senkes til 80 etter testing
MEDIUM_THRESHOLD = 60        # Kan justeres
```

### Polling Intervals

**Orchestrator:**
```python
# orchestrator.py
self.polling_interval = 30  # sekunder
```

**Workers:**
```python
# worker.py  
polling_interval = 5  # sekunder (når ingen tasks)
```

---

## ⚡ Performance

### Estimert gjennomstrømning

Med Claude Sonnet (production):
- Invoice Parser: ~100 fakturaer/time
- Bookkeeping: ~50 bokføringer/time
- Learning: ~200 korreksjoner/time

### Skalering

Kjør flere workers av samme type for parallellprosessering:

```bash
# 3 bookkeeper workers for høyere throughput
python -m app.agents.worker bookkeeper &
python -m app.agents.worker bookkeeper &
python -m app.agents.worker bookkeeper &
```

Tasks claimes atomisk (FOR UPDATE SKIP LOCKED), så ingen race conditions.

### Cost Estimate

Med Claude Sonnet-3.5 (~$3 per million input tokens):

500 fakturaer/måned:
- Invoice Parser: ~500 × 2000 tokens = 1M tokens = ~$3
- Bookkeeper: ~500 × 3000 tokens = 1.5M tokens = ~$5
- **Total: ~$8-10/måned per klient**

---

## 🐛 Known Limitations & TODOs

### Nå (MVP)

✅ Komplett event-driven flyt  
✅ Pattern learning fra corrections  
✅ Auto-approve high-confidence  
✅ Review queue for low-confidence  
✅ Audit trail  
✅ Error handling & retry  

### Mangler (kan legges til senere)

❌ Batch correction execution (learning agent finner lignende, men utfører ikke auto-fix)  
❌ Pattern deactivation (success_rate < 50%)  
❌ Avstemming-agent (fase 2)  
❌ Period closing checks (fase 2)  
❌ Multi-tenant pattern sharing (fase 3)  
❌ PDF invoice parsing (OCR)  

### Edge Cases å teste

- [ ] Unbalanced entries (debit != credit)
- [ ] Duplicate invoices
- [ ] Unknown vendors
- [ ] Missing VAT
- [ ] Multi-currency
- [ ] Negative amounts (credit notes)
- [ ] Very large amounts

---

## 📚 Neste steg

### 1. Database Migrations

Kjør Alembic autogenerate for de tre nye modellene.

### 2. Integration med Frontend

Review Queue UI må hente data fra `review_queue` tabell og vise:
- AI suggestion
- AI reasoning
- Confidence score
- Approve/Correct actions

### 3. Correction API

Når regnskapsfører korrigerer, må backend:
1. Opprette `Correction` record
2. Reversere original `GeneralLedger`
3. Opprette ny korrekt `GeneralLedger`
4. Publisere `correction_received` event
5. Learning agent vil plukke opp og lære

### 4. Testing med real data

- Importer test-fakturaer (EHF XML)
- Kjør gjennom hele flyten
- Evaluer confidence scores
- Juster thresholds

### 5. Deployment

- Systemd services for hver agent
- Health checks
- Monitoring (Prometheus/Grafana)
- Log aggregation

---

## 💡 Tips & Tricks

### Quick restart all agents

```bash
# Kill all
pkill -f "app.agents"

# Restart
python -m app.agents.run_orchestrator &
python -m app.agents.worker invoice_parser &
python -m app.agents.worker bookkeeper &
python -m app.agents.worker learning &
```

### Watch agent activity in real-time

```bash
# Terminal 1: Tail orchestrator logs
python -m app.agents.run_orchestrator 2>&1 | tee orchestrator.log

# Terminal 2: Watch events
watch -n 1 'psql kontali -c "SELECT COUNT(*) FROM agent_events WHERE processed=false"'

# Terminal 3: Watch tasks  
watch -n 1 'psql kontali -c "SELECT agent_type, status, COUNT(*) FROM agent_tasks GROUP BY agent_type, status"'
```

### Manual event injection for testing

```python
from app.models.agent_event import AgentEvent
from app.database import async_session

async with async_session() as db:
    event = AgentEvent(
        tenant_id="...",
        event_type="invoice_received",
        payload={"invoice_id": "..."}
    )
    db.add(event)
    await db.commit()
```

---

## ✅ Checklist før production

- [ ] Database migrations kjørt
- [ ] ANTHROPIC_API_KEY satt (production key)
- [ ] Confidence thresholds testet og justert
- [ ] Error notifications oppsett (Slack/email)
- [ ] Monitoring dashboards (Grafana)
- [ ] Health check endpoints
- [ ] Systemd service files
- [ ] Backup strategy for agent_events/tasks
- [ ] Log rotation konfigurert
- [ ] Rate limiting for Claude API
- [ ] Cost monitoring oppsett

---

**Ferdig!** 🎉

Systemet er komplett implementert i henhold til ARCHITECTURE.md.
Alle 4 hovedkomponenter (Orchestrator + 3 specialist agents) er bygget,
testet (med mocks), dokumentert og klar for integrasjon med eksisterende backend.
