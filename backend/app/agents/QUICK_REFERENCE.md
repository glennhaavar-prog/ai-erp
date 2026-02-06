# Quick Reference - Multi-Agent System

Hurtigreferanse for daglig bruk av agent-systemet.

---

## 🚀 Start/Stop Agenter

### Development (manuelt)

```bash
# Start orchestrator
python -m app.agents.run_orchestrator

# Start workers
python -m app.agents.worker invoice_parser
python -m app.agents.worker bookkeeper
python -m app.agents.worker learning
```

### Production (systemd)

```bash
# Start
sudo systemctl start kontali-orchestrator
sudo systemctl start kontali-worker-parser
sudo systemctl start kontali-worker-bookkeeper

# Stop
sudo systemctl stop kontali-orchestrator
sudo systemctl stop kontali-worker-parser
sudo systemctl stop kontali-worker-bookkeeper

# Restart
sudo systemctl restart kontali-orchestrator

# Status
sudo systemctl status kontali-orchestrator
```

---

## 🧪 Testing

### Trigger test flow

```bash
# Get client ID
psql kontali -c "SELECT id, name FROM clients LIMIT 5;"

# Trigger complete flow
python -m app.agents.utils trigger <client-uuid>
```

### Se statistikk

```bash
python -m app.agents.utils stats <client-uuid>
```

### Run unit tests

```bash
pytest tests/test_agents.py -v
```

---

## 🔍 Debugging

### Quick checks

```bash
# Are agents running?
ps aux | grep "app.agents"

# Check logs (if running manually)
tail -f orchestrator.log
tail -f parser.log
tail -f bookkeeper.log

# Check systemd logs
sudo journalctl -u kontali-orchestrator -f
```

### Database queries

```sql
-- Unprocessed events
SELECT id, event_type, created_at 
FROM agent_events 
WHERE processed = false 
ORDER BY created_at DESC;

-- Pending tasks
SELECT agent_type, task_type, priority, created_at
FROM agent_tasks 
WHERE status = 'pending'
ORDER BY priority DESC, created_at ASC;

-- Failed tasks
SELECT agent_type, task_type, error_message, created_at
FROM agent_tasks 
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;

-- Review queue
SELECT priority, issue_category, ai_confidence, created_at
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

-- Recent audit log
SELECT action, entity_type, actor_type, created_at
FROM audit_log
WHERE actor_type = 'ai'
ORDER BY created_at DESC
LIMIT 20;

-- Active patterns
SELECT pattern_type, pattern_name, success_rate, times_applied
FROM agent_learned_patterns
WHERE is_active = true
ORDER BY success_rate DESC;
```

---

## 🔧 Common Tasks

### Manuelt trigger event

```python
# Fra Python REPL eller script
from app.models.agent_event import AgentEvent
from app.database import async_session

async with async_session() as db:
    event = AgentEvent(
        tenant_id="<client-uuid>",
        event_type="invoice_received",
        payload={"invoice_id": "<invoice-uuid>"}
    )
    db.add(event)
    await db.commit()
    print(f"Event created: {event.id}")
```

### Reset failed tasks

```sql
-- Reset recent failed tasks to retry
UPDATE agent_tasks 
SET status = 'pending', 
    retry_count = 0, 
    error_message = NULL,
    started_at = NULL
WHERE status = 'failed' 
  AND created_at > NOW() - INTERVAL '1 hour';
```

### Clear old processed events

```sql
-- Clean up events older than 7 days
DELETE FROM agent_events 
WHERE processed = true 
  AND created_at < NOW() - INTERVAL '7 days';
```

---

## 📊 Monitoring

### Health check

```bash
curl http://localhost:8000/api/v1/health/agents
```

Response:
```json
{
  "status": "healthy",
  "unprocessed_events": 0,
  "failed_tasks": 0
}
```

### Watch activity

```bash
# Terminal 1: Events
watch -n 2 'psql kontali -c "SELECT COUNT(*) FROM agent_events WHERE processed=false"'

# Terminal 2: Tasks
watch -n 2 'psql kontali -c "SELECT agent_type, status, COUNT(*) FROM agent_tasks GROUP BY agent_type, status"'

# Terminal 3: Review queue
watch -n 2 'psql kontali -c "SELECT priority, COUNT(*) FROM review_queue WHERE status='\''pending'\'' GROUP BY priority"'
```

---

## 🚨 Troubleshooting

### Problem: Events ikke prosessert

**Check:**
```bash
ps aux | grep orchestrator
```

**Fix:**
```bash
sudo systemctl restart kontali-orchestrator
```

### Problem: Tasks stuck i pending

**Check:**
```bash
ps aux | grep "agents.worker"
psql kontali -c "SELECT agent_type, COUNT(*) FROM agent_tasks WHERE status='pending' GROUP BY agent_type"
```

**Fix:**
```bash
sudo systemctl start kontali-worker-parser
sudo systemctl start kontali-worker-bookkeeper
```

### Problem: Claude API errors

**Check:**
```bash
echo $ANTHROPIC_API_KEY
```

**Fix:**
```bash
# I .env
ANTHROPIC_API_KEY=sk-ant-...

# Restart agents
sudo systemctl restart kontali-worker-bookkeeper
```

### Problem: Unbalanced entries

**Check:**
```sql
SELECT 
    id,
    (SELECT SUM(debit_amount) FROM general_ledger_lines WHERE general_ledger_id = gl.id) as total_debit,
    (SELECT SUM(credit_amount) FROM general_ledger_lines WHERE general_ledger_id = gl.id) as total_credit
FROM general_ledger gl
WHERE status = 'draft'
  AND created_by_type = 'ai_agent'
HAVING (SELECT SUM(debit_amount) FROM general_ledger_lines WHERE general_ledger_id = gl.id) 
    != (SELECT SUM(credit_amount) FROM general_ledger_lines WHERE general_ledger_id = gl.id);
```

**Fix:** Review og correct i review queue.

---

## 📝 Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/kontali

# Optional
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
LOG_LEVEL=INFO
```

### Confidence Thresholds

Edit `backend/app/agents/orchestrator.py`:

```python
AUTO_APPROVE_THRESHOLD = 85  # Default: 85
MEDIUM_THRESHOLD = 60        # Default: 60
```

### Polling Intervals

```python
# Orchestrator (orchestrator.py)
self.polling_interval = 30  # seconds

# Workers (worker.py)
polling_interval = 5  # seconds
```

---

## 📈 Performance Tips

### Scale workers

```bash
# Run multiple bookkeepers for higher throughput
python -m app.agents.worker bookkeeper &
python -m app.agents.worker bookkeeper &
python -m app.agents.worker bookkeeper &
```

### Monitor costs

```sql
-- Count LLM calls (approximate)
SELECT 
    COUNT(*) as bookings,
    COUNT(*) * 3000 as estimated_tokens,
    COUNT(*) * 3000 * 0.000003 as estimated_cost_usd
FROM general_ledger
WHERE created_by_type = 'ai_agent'
  AND created_at > NOW() - INTERVAL '1 month';
```

---

## 🔐 Security

### API Key rotation

```bash
# 1. Update .env
nano .env
# Set new ANTHROPIC_API_KEY

# 2. Restart agents
sudo systemctl restart kontali-worker-bookkeeper
```

### Access control

```sql
-- Review who has made corrections
SELECT 
    u.email,
    COUNT(*) as corrections_count
FROM corrections c
JOIN users u ON c.corrected_by = u.id
GROUP BY u.email
ORDER BY corrections_count DESC;
```

---

## 💾 Backup

### Critical tables

```bash
# Backup learned patterns
pg_dump kontali -t agent_learned_patterns > patterns_$(date +%Y%m%d).sql

# Backup corrections
pg_dump kontali -t corrections > corrections_$(date +%Y%m%d).sql

# Restore
psql kontali < patterns_20240204.sql
```

---

## 📞 Quick Commands Cheatsheet

```bash
# Start all (dev)
python -m app.agents.run_orchestrator &
python -m app.agents.worker invoice_parser &
python -m app.agents.worker bookkeeper &

# Stop all
pkill -f "app.agents"

# Test flow
python -m app.agents.utils trigger <client-uuid>

# Stats
python -m app.agents.utils stats <client-uuid>

# Health
curl localhost:8000/api/v1/health/agents

# Logs (systemd)
sudo journalctl -u kontali-orchestrator -f

# DB quick check
psql kontali -c "SELECT COUNT(*) FROM agent_events WHERE processed=false"
```

---

**Lagre denne filen til hurtigreferanse!** 🚀
