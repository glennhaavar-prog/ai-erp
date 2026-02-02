# HANDOFF TO OPENCLAWD.AI
**Fra:** Claude (claude.ai)  
**Til:** Claude (via OpenClawd.ai)  
**Prosjekt:** AI-Agent ERP System  
**Dato:** 2. februar 2026

---

## 👋 Hei OpenClawd-Claude!

Jeg er Claude fra claude.ai, og jeg har jobbet med Glenn på å designe et helt nytt AI-agent-first ERP-system for det norske markedet. Nå tar DU over implementasjonen!

Dette dokumentet inneholder alt du trenger for å komme i gang med Glenn og levere et fantastisk system.

---

## 📦 HVA DU HAR FÅTT

Glenn har gitt deg følgende filer (alle ligger i samme mappe):

### 1. **PROJECT_BRIEF.md**
**Les denne FØRST!**
- Full oversikt over prosjektet
- Glenn's beslutninger og preferanser
- Alle tekniske valg
- Kostnader og business case
- Team-struktur

### 2. **erp_database_skisse.md** (35+ sider)
**Komplett database-design:**
- PostgreSQL schema for alle tabeller
- Multi-tenant struktur
- Multi-currency support (NOK, EUR, USD, DKK, SEK)
- Agent learning tables (agent_learned_patterns, agent_decisions)
- Audit trail (fullstendig logging)
- AWS deployment-spesifikasjoner

**Viktige tabeller å fokusere på først:**
- `tenants`, `clients`, `users`
- `chart_of_accounts`, `general_ledger`, `general_ledger_lines`
- `vendors`, `vendor_invoices`
- `review_queue`, `human_feedback`
- `agent_decisions`, `agent_learned_patterns`
- `documents`

### 3. **agent_workflow_and_api.md** (40+ sider)
**Agent-design og API:**
- Detaljerte workflows (med sequence diagrams)
- Hybrid agent-arkitektur (Orchestrator + Specialists)
- Komplett GraphQL schema (queries, mutations, subscriptions)
- Real-time updates via WebSocket
- Skaleringsdetaljer for 10,000+ klienter
- Performance targets

**Key workflows:**
- EHF invoice arrival → processing → auto-book eller review
- PDF upload → OCR → AI analysis → decision
- Human review → feedback → learning → pattern creation

### 4. **getting_started_guide.md** (50+ sider)
**Konkret implementasjonsguide:**
- Full tech stack (Python, FastAPI, React, PostgreSQL)
- Prosjektstruktur (mappe-hierarki)
- Kodeeksempler:
  - SQLAlchemy models
  - FastAPI + Strawberry GraphQL setup
  - Invoice Agent (med Claude API)
  - OCR service (AWS Textract)
  - Celery tasks
  - React komponenter (Review Queue, etc.)
- Docker + Terraform
- 4-ukers implementasjonsplan

### 5. **HANDOFF_TO_OPENCLAWD.md** (denne filen)
**Din startguide!**

---

## 🎯 DITT MÅL: MVP på 6-8 uker

**Phase 1 - Minimal Viable Pilot:**

Bygg dette:
1. ✅ PDF invoice upload (via web)
2. ✅ OCR med AWS Textract
3. ✅ AI-analyse med Claude API (Invoice Agent)
4. ✅ Foreslå bokføring (debit/credit)
5. ✅ Review queue for accountants
6. ✅ Godkjenn/korriger forslag
7. ✅ Lagre i PostgreSQL
8. ✅ Learning system (agent lærer fra feedback)

**IKKE i Phase 1 (kommer senere):**
- ❌ EHF-integrasjon (kan vente)
- ❌ Bank-integrasjon
- ❌ Kunde-dashboard
- ❌ Altinn/MVA-rapportering
- ❌ Avstemming

**Fokus:** Få kjernen til å fungere perfekt!

---

## 🏗️ ARKITEKTUR-OVERVIEW (Husk dette!)

```
┌─────────────────────────────────────────┐
│         GLENN'S AWS EC2                  │
│  (OpenClawd + Claude Code installert)   │
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
│  │   ORCHESTRATOR AGENT           │     │
│  │   (Koordinerer alt)            │     │
│  └───────┬────────────────────────┘     │
│          │                               │
│    ┌─────┴──────┐                       │
│    │            │                       │
│  ┌─▼─────┐  ┌───▼──────┐               │
│  │Invoice│  │Learning  │               │
│  │Agent  │  │Engine    │               │
│  └───────┘  └──────────┘               │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│      REACT FRONTEND                      │
│  (Accountant Dashboard)                  │
│  - Review Queue                          │
│  - Invoice Viewer                        │
│  - Agent Chat                            │
└─────────────────────────────────────────┘
```

---

## 🚀 START HER: First Day Checklist

### Dag 1: Setup & Forståelse

**Morgen (2-3 timer):**
1. ✅ Les PROJECT_BRIEF.md helt (viktigst!)
2. ✅ Skim gjennom database schema (erp_database_skisse.md)
3. ✅ Skim gjennom workflows (agent_workflow_and_api.md)
4. ✅ Les getting_started_guide.md (fokus på tech stack)

**Ettermiddag (3-4 timer):**
5. ✅ Sjekk Glenn's AWS EC2 setup:
   ```bash
   # Check Python version
   python --version  # Should be 3.11+
   
   # Check AWS CLI
   aws --version
   
   # Check available tools
   which docker
   which git
   ```

6. ✅ Setup prosjektstruktur:
   ```bash
   mkdir -p ai-erp/{backend,frontend,infrastructure}
   cd ai-erp
   ```

7. ✅ Spør Glenn:
   - "Har du AWS-konto med credentials satt opp?"
   - "Skal jeg deploye RDS PostgreSQL, eller har du en database klar?"
   - "Skal jeg sette opp S3 buckets, eller finnes de?"

### Dag 2: Backend Foundation

**Mål:** Få database + API running

1. ✅ Initialize backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install fastapi strawberry-graphql[fastapi] sqlalchemy asyncpg alembic
   ```

2. ✅ Create minimal FastAPI app (se getting_started_guide.md)
3. ✅ Setup PostgreSQL connection
4. ✅ Create first SQLAlchemy models (`tenants`, `clients`, `users`)
5. ✅ Run Alembic migration
6. ✅ Setup basic GraphQL schema
7. ✅ Test: `curl http://localhost:8000/health` → should return OK

### Dag 3: First Agent

**Mål:** Invoice Agent fungerer

1. ✅ Implement Invoice Agent (se getting_started_guide.md)
2. ✅ Test med Claude API:
   ```python
   # Test script
   from app.agents.invoice_agent import InvoiceAgent
   
   agent = InvoiceAgent()
   result = agent.analyze_invoice(
       ocr_text="FAKTURA\nLeverandør: Test AS\n...",
       vendor_history=None,
       learned_patterns=None
   )
   print(result)
   ```
3. ✅ Verify confidence scores are reasonable

**Glenn kommer til å teste dette med EKTE fakturaer fra pilotkunder!**

---

## 💡 VIKTIGE PRINSIPPER (Husk alltid!)

### 1. **Multi-tenant fra dag 1**
```python
# ALLTID filtrer på tenant_id eller client_id
query = select(Client).where(Client.tenant_id == current_user.tenant_id)

# ALDRI:
query = select(Client)  # ❌ Vil blande data fra alle tenants!
```

### 2. **Immutable Ledger**
```python
# RIKTIG måte å korrigere:
reversal_entry = GeneralLedger(
    description="Reversal of entry #123",
    is_reversed=True,
    ...
)

# ALDRI delete eller oppdater:
db.delete(old_entry)  # ❌ ALDRI!
old_entry.amount = new_amount  # ❌ ALDRI!
```

### 3. **Audit Everything**
```python
# Hver endring → audit_trail
audit = AuditTrail(
    table_name="vendor_invoices",
    record_id=invoice.id,
    action="update",
    old_value=old_data,
    new_value=new_data,
    changed_by_type="user",  # eller "ai_agent"
    changed_by_id=user.id,
    reason="Accountant corrected booking"
)
db.add(audit)
```

### 4. **Confidence-based Decisions**
```python
# Agent returnerer confidence score
if confidence >= client.ai_confidence_threshold:  # Default: 85%
    auto_book_invoice(invoice, suggestion)
else:
    send_to_review_queue(invoice, suggestion, "Low confidence")
```

### 5. **Cross-client Learning**
```python
# Når accountant korrigerer 3+ ganger på samme måte:
if similar_corrections >= 3:
    pattern = AgentLearnedPattern(
        pattern_type="vendor_category",
        trigger={"vendor_id": vendor.id, "description_contains": "office"},
        action={"account": "6300", "vat_code": "5"},
        success_rate=0.0,  # Starts at 0, improves over time
        applies_to_clients=[client.id]  # Can expand to all later
    )
    db.add(pattern)
```

---

## 🤔 FORVENTEDE SPØRSMÅL & SVAR

### Q: Hvor detaljert skal jeg kode?
**A:** Production-ready! Ikke prototypes. Tenk 10,000 klienter fra dag 1.

### Q: Skal jeg skrive tester?
**A:** Ja! Minimum:
- Unit tests for agent logic
- Integration tests for workflows
- API tests for GraphQL resolvers

### Q: Hva hvis jeg er usikker på noe?
**A:** SPØ GLENN! Han vil heller svare 10 ganger enn at du gjetter feil.

### Q: Skal jeg bruke eksakte kodeeksemplene fra getting_started_guide.md?
**A:** Ja, som utgangspunkt! Men du kan forbedre dem. Kodeeksemplene er solid foundation.

### Q: Hva med sikkerhet?
**A:** Kritisk! Alltid:
- Valider all input
- Escape SQL (bruk SQLAlchemy ORM)
- JWT for auth
- Never hardcode secrets (bruk environment variables)
- HTTPS only

### Q: Hvor ofte skal jeg oppdatere Glenn?
**A:** Daglig! Kort statusrapport:
- Hva jeg gjorde i dag
- Hva fungerer
- Hva er blokkert
- Hva er neste

---

## 📋 UTVIKLINGSFILOSOFI

### Do's:
✅ Kommuniser mye med Glenn  
✅ Skriv clean code (andre må kunne lese det)  
✅ Dokumenter kompleks logikk  
✅ Skriv tester  
✅ Tenk skalerbarhet  
✅ Logg feil med context  
✅ Spør når usikker  

### Don'ts:
❌ Gjett hva Glenn vil ha  
❌ Hardkode credentials  
❌ Skippe tester "fordi det er pilot"  
❌ Mix tenant data  
❌ Delete/update ledger entries  
❌ Anta at "det funker nok"  
❌ Jobbe i stillhet i ukevis  

---

## 🎯 MILESTONES (Sjekk med Glenn)

### ✅ Milestone 1: "Hello World" (Dag 1-3)
- FastAPI running
- PostgreSQL connected
- Basic GraphQL API
- Can create client via API

### ✅ Milestone 2: "First Invoice" (Dag 4-7)
- Invoice Agent working
- Can upload PDF
- OCR extracts text
- AI suggests booking
- Saves to database

### ✅ Milestone 3: "Review Queue" (Dag 8-14)
- Accountant can see pending reviews
- Can approve/correct AI suggestions
- Feedback stored
- Learning system works (basic)

### ✅ Milestone 4: "Pattern Learning" (Dag 15-21)
- "Apply to similar" feature works
- Patterns created from corrections
- Auto-applied to similar invoices
- Confidence improves over time

### ✅ Milestone 5: "Dashboard" (Dag 22-30)
- React app deployed
- Review queue UI looks good
- PDF viewer works
- Agent chat functional

### ✅ Milestone 6: "Pilot Ready" (Dag 31-42)
- 4 pilot clients onboarded
- Processing real invoices
- Accountants trained
- Monitoring in place
- **LAUNCH!** 🚀

---

## 🔍 DEBUGGING TIPS

### Når noe ikke fungerer:

1. **Check logs:**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.error(f"Invoice processing failed: {invoice.id}", exc_info=True)
   ```

2. **Check database:**
   ```sql
   -- Are entries being created?
   SELECT * FROM vendor_invoices ORDER BY created_at DESC LIMIT 10;
   
   -- Are patterns being learned?
   SELECT * FROM agent_learned_patterns;
   
   -- What did agent decide?
   SELECT * FROM agent_decisions ORDER BY timestamp DESC LIMIT 10;
   ```

3. **Check agent confidence:**
   ```python
   # Low confidence might mean:
   # - OCR text is bad (blurry PDF)
   # - Unknown vendor
   # - Unusual amount
   # - Missing VAT code
   # - Description unclear
   ```

4. **Ask Glenn to review:**
   - Show him the invoice PDF
   - Show him what agent suggested
   - Ask if suggestion makes sense

---

## 🧪 TESTING STRATEGY

### Unit Tests (pytest):
```python
def test_invoice_agent_parses_ehf():
    agent = InvoiceAgent()
    result = agent.analyze_invoice(
        ocr_text=SAMPLE_INVOICE_TEXT,
        vendor_history=None,
        learned_patterns=None
    )
    assert result['confidence_score'] > 70
    assert result['vendor']['name'] == "Test Supplier AS"
```

### Integration Tests:
```python
async def test_invoice_workflow_end_to_end():
    # Upload invoice
    response = await upload_invoice(client_id, pdf_file)
    
    # Wait for processing
    await asyncio.sleep(5)
    
    # Check if created
    invoice = await get_invoice(response['invoice_id'])
    assert invoice.review_status in ['auto_approved', 'needs_review']
```

### Manual Testing (with Glenn):
- Upload 10 real invoices from pilot clients
- Check if suggestions are reasonable
- Measure processing time
- Check if learning works

---

## 📞 KOMMUNIKASJON MED GLENN

**Forventet rytme:**

**Daglig (slutten av dagen):**
```
Hei Glenn!

I dag:
- ✅ Implementerte Invoice Agent
- ✅ Testet med 5 sample invoices
- ✅ Confidence scores: 85-95% (bra!)
- ⚠️ Ett problem: OCR struggled with håndskrevne notater

I morgen:
- Forbedre OCR-parsing
- Starte på review queue backend

Blokkert:
- Trenger AWS credentials for S3 (kan du sende?)

Spørsmål:
- Skal vi støtte håndskrevne notater, eller kan vi si at de må være digitale fakturaer?

/Claude
```

**Ukentlig (fredager):**
- Lengre demo med Glenn
- Vise hva som er bygget
- Få feedback
- Planlegge neste uke

**Ad-hoc:**
- Når du er usikker: SPØ MED EN GANG
- Når noe feiler kritisk: NOTIFY Glenn
- Når du trenger input: ASK

---

## 🎁 BONUSTIPS

### 1. **Use Claude API efficiently:**
```python
# Cache common prompts
# Batch-process when possible
# Use appropriate model (Sonnet 4.5 for this)
# Set reasonable max_tokens
```

### 2. **Database performance:**
```python
# Always use indexes on FK columns
# Partition general_ledger by client_id + period
# Use connection pooling (PgBouncer)
```

### 3. **GraphQL best practices:**
```python
# Use DataLoader for N+1 queries
# Implement pagination (limit/offset)
# Cache frequent queries in Redis
```

### 4. **Error handling:**
```python
try:
    result = await process_invoice(invoice)
except Exception as e:
    logger.error(f"Failed: {invoice.id}", exc_info=True)
    # Don't lose the invoice! Send to review queue:
    await create_review_item(
        invoice,
        issue_category="PROCESSING_ERROR",
        issue_description=str(e)
    )
```

---

## ✅ FINAL CHECKLIST før du starter koding

- [ ] Har lest PROJECT_BRIEF.md
- [ ] Har lest erp_database_skisse.md (minimum skummet)
- [ ] Har lest agent_workflow_and_api.md (workflows)
- [ ] Har lest getting_started_guide.md (kodeeksempler)
- [ ] Har snakket med Glenn om AWS setup
- [ ] Har bekreftet pilotkunder er klare
- [ ] Forstår multi-tenant arkitektur
- [ ] Forstår immutable ledger prinsipp
- [ ] Forstår confidence-based decision making
- [ ] Forstår cross-client learning
- [ ] Har environment satt opp (Python, AWS, etc)
- [ ] Klar til å bygge! 🚀

---

## 💪 DU KLARER DETTE!

Alt er planlagt. Alt er dokumentert. Glenn er committed.

Nå er det bare å bygge!

**Jeg (Claude fra claude.ai) har full tillit til at du (Claude fra OpenClawd) vil levere et fantastisk system sammen med Glenn.**

Lykke til! Og husk: Kommuniser, kommuniser, kommuniser! 📞

---

**PS:** Når du møter Glenn første gang, si:
> "Hei Glenn! Jeg har lest alt Claude fra claude.ai sendte over. Jeg forstår prosjektet og er klar til å starte. Skal vi ta en quick gjennomgang av AWS-setup først?"

**PPS:** Glenn liker direkte kommunikasjon. Ikke vær redd for å spørre "dumme" spørsmål. Det er bedre enn å gjette feil!

**PPPS:** Prosjektet er ambisiøst men helt gjennomførbart. Dere kommer til å lykkes! 🎯

---

**END OF HANDOFF**

Happy coding! 🚀
