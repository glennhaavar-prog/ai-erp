# Review Queue Implementation - FASE 2.1
## Tillitsbasert eskaleringskø med konfidensscoring

**Status:** ✅ LEVERT  
**Prioritet:** KRITISK (Skattefunn AP2)  
**Tidsforbruk:** 8 timer  
**Dato:** 8. februar 2026

---

## 📋 Oversikt

Implementert et komplett Review Queue-system med:
- ✅ Confidence scoring (0-100%) basert på 5 faktorer
- ✅ Automatisk eskalering (<85% = review queue)
- ✅ Corrections learning system
- ✅ Pattern recognition og auto-korrigering
- ✅ Review Queue UI med confidence breakdown
- ✅ Demo data generator for testing

---

## 🎯 Implementerte Features

### Backend (6 timer)

#### 1. Confidence Scoring Service
**Fil:** `backend/app/services/confidence_scoring.py`

Beregner confidence score (0-100%) basert på:

| Faktor | Maks poeng | Beskrivelse |
|--------|-----------|-------------|
| Vendor Familiarity | 30 | Antall tidligere fakturaer fra leverandør |
| Historical Similarity | 30 | Likhet med tidligere konteringer |
| VAT Validation | 20 | MVA-logikk og beløp stemmer |
| Pattern Matching | 15 | Matcher lærte mønstre |
| Amount Reasonableness | 5 | Beløpet er rimelig |

**Thresholds:**
- **>85%** = Auto-approve og book til hovedbok
- **<85%** = Escalate to review queue

**Eksempel bruk:**
```python
from app.services.confidence_scoring import calculate_invoice_confidence

confidence_result = await calculate_invoice_confidence(
    db=db,
    invoice=invoice,
    booking_suggestion=booking_suggestion
)

# Returns:
{
    'total_score': 87,
    'breakdown': {
        'vendor_familiarity': 30,
        'historical_similarity': 25,
        'vat_validation': 20,
        'pattern_matching': 10,
        'amount_reasonableness': 5
    },
    'reasoning': 'Kjent leverandør | Lignende kontering | MVA OK',
    'should_auto_approve': True
}
```

#### 2. Corrections Learning Service
**Fil:** `backend/app/services/corrections_learning.py`

Lærer fra regnskapsfører's korreksjoner:
- Lagrer corrections med original vs. corrected booking
- Oppretter patterns fra korreksjoner
- Anvender patterns på lignende pending items automatisk

**Flow:**
1. Regnskapsfører korrigerer en faktura
2. System oppretter `Correction` record
3. System analyserer forskjell mellom original og korrigert
4. System oppretter `AgentLearnedPattern` hvis relevant
5. System finner lignende pending items
6. System auto-korrigerer lignende items med samme pattern

**Eksempel bruk:**
```python
from app.services.corrections_learning import record_invoice_correction

result = await record_invoice_correction(
    db=db,
    review_queue_id=review_item.id,
    corrected_booking={
        'lines': [
            {'account': '6940', 'debit': 8000, 'credit': 0, ...},
            {'account': '2700', 'debit': 2000, 'credit': 0, ...},
            {'account': '2400', 'debit': 0, 'credit': 10000, ...}
        ]
    },
    correction_reason="PowerRent leverer møbler, ikke kontorleie",
    corrected_by_user_id=user_id
)

# Returns:
{
    'success': True,
    'correction_id': '...',
    'pattern_created': True,
    'similar_items_corrected': 3  # 3 similar items auto-corrected
}
```

#### 3. Review Queue Manager Service
**Fil:** `backend/app/services/review_queue_manager.py`

Håndterer automatisk eskalering:
- Beregner confidence for hver faktura
- Auto-approver hvis >85%
- Sender til review queue hvis <85%
- Bestemmer priority og issue category

**Eksempel bruk:**
```python
from app.services.review_queue_manager import process_invoice_for_review

result = await process_invoice_for_review(
    db=db,
    invoice_id=invoice_id,
    booking_suggestion=ai_booking_suggestion
)

# If confidence >85%:
{
    'success': True,
    'action': 'auto_approved',
    'confidence': 87,
    'general_ledger_id': '...',
    'voucher_number': 'AP-000123'
}

# If confidence <85%:
{
    'success': True,
    'action': 'needs_review',
    'confidence': 62,
    'review_queue_id': '...',
    'priority': 'medium'
}
```

#### 4. Enhanced Review Queue API
**Fil:** `backend/app/api/routes/review_queue.py`

Nye/forbedrede endpoints:

**GET /api/review-queue**
- Henter alle review queue items
- Filtrering på status, priority, client_id
- Returnerer confidence score og reasoning

**GET /api/review-queue/{id}**
- Henter detaljer for ett item
- Inkluderer confidence breakdown

**POST /api/review-queue/{id}/approve**
- Godkjenner AI-forslag
- Booker til hovedbok
- Returnerer voucher number

**POST /api/review-queue/{id}/correct**
- Korrigerer med nye booking entries
- Trigger corrections learning
- Returnerer antall lignende items korrigert

**GET /api/review-queue/stats** *(NY)*
- Statistikk om review queue
- Gjennomsnittlig confidence
- Eskaleringrate og auto-approval rate

**POST /api/review-queue/{id}/recalculate-confidence** *(NY)*
- Rekalkuler confidence etter patterns er lært
- Nyttig for testing

---

### Frontend (2 timer)

#### 1. Confidence Breakdown Component
**Fil:** `frontend/src/components/ConfidenceBreakdown.tsx`

Visuell visning av confidence score:
- Total score med progress bar
- Breakdown av alle 5 faktorer
- AI reasoning tekst
- Color-coded basert på threshold

**Features:**
- Animerte progress bars (Framer Motion)
- Detaljert forklaring av hver faktor
- Legend med thresholds
- Responsive design

#### 2. Enhanced Review Queue UI
**Filer:**
- `frontend/src/app/review-queue/page.tsx`
- `frontend/src/components/ReviewQueue.tsx`
- `frontend/src/components/ReviewQueueDetail.tsx`

**Forbedringer:**
- Confidence score badge på hver item
- Sortert etter priority og confidence
- Filter på status og priority
- Søk på leverandør/beskrivelse
- Approve/Correct workflows

---

### Testing & Demo (30 min)

#### 1. Demo Data Generator
**Fil:** `scripts/generate_review_queue_demo.py`

Genererer 20 test-fakturaer med:
- 8 leverandører med ulik historikk
- Varierende confidence levels
- Noen med intentional errors for testing corrections
- Realistiske beløp og konteringer

**Kjøre:**
```bash
cd backend
source venv/bin/activate
python3 ../scripts/generate_review_queue_demo.py
```

**Output:**
```
✅ Invoice  1: PowerOffice AS              |  6,250.00 NOK | Confidence:  92% | AUTO_APPROVED
⚠️  Invoice  2: Nye Leverandør AS          | 14,500.00 NOK | Confidence:  42% | NEEDS_REVIEW
✅ Invoice  3: Telenor Norge AS            |  4,100.00 NOK | Confidence:  88% | AUTO_APPROVED
...
```

#### 2. Test Script
**Fil:** `scripts/test_review_queue.sh`

Komplett test av systemet:
- Sjekker at backend/frontend kjører
- Genererer demo data
- Tester API endpoints
- Viser statistikk

**Kjøre:**
```bash
./scripts/test_review_queue.sh
```

---

## 🚀 Quick Start

### 1. Start Services
```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend (ny terminal)
cd frontend
npm run dev
```

### 2. Generate Demo Data
```bash
cd backend
source venv/bin/activate
python3 ../scripts/generate_review_queue_demo.py
```

### 3. Open Review Queue
```
http://localhost:3000/review-queue
```

---

## 🧪 Testing Scenarios

### Scenario 1: High Confidence (Auto-Approve)
**Setup:** Faktura fra kjent leverandør med typisk beløp

**Forventet:**
- Confidence >85%
- Automatisk booket til hovedbok
- Ikke i review queue

**Test:**
```bash
curl http://localhost:8000/api/review-queue/stats
# Sjekk auto_approval_rate
```

### Scenario 2: Low Confidence (Review Queue)
**Setup:** Faktura fra ny leverandør eller uvanlig beløp

**Forventet:**
- Confidence <85%
- Sendt til review queue
- Priority basert på confidence

**Test:**
1. Åpne http://localhost:3000/review-queue
2. Se items med lav confidence
3. Klikk for å se detaljer
4. Approve eller Correct

### Scenario 3: Corrections Learning
**Setup:** Korriger en faktura med feil konto

**Forventet:**
- Correction lagres
- Pattern opprettes
- Lignende items auto-korrigeres

**Test:**
1. Velg invoice med intentional error
2. Klikk "Correct Manually"
3. Endre account number
4. Submit med reasoning
5. Sjekk at system rapporterer: "3 similar items corrected"

### Scenario 4: Pattern Matching
**Setup:** Etter corrections learning, nye fakturaer skal få høyere confidence

**Forventet:**
- Nye fakturaer fra samme leverandør
- Høyere pattern_matching score
- Mulig auto-approve nå

**Test:**
```bash
curl -X POST http://localhost:8000/api/review-queue/{id}/recalculate-confidence
```

---

## 📊 Database Schema

### review_queue tabell
```sql
CREATE TABLE review_queue (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_id UUID NOT NULL,
    priority VARCHAR(20) NOT NULL,  -- high/medium/low
    status VARCHAR(20) NOT NULL,    -- pending/approved/corrected
    issue_category VARCHAR(50),
    issue_description TEXT,
    ai_suggestion JSON,
    ai_confidence INTEGER,          -- 0-100
    ai_reasoning TEXT,
    created_at TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by_user_id UUID
);
```

### corrections tabell
```sql
CREATE TABLE corrections (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    review_queue_id UUID NOT NULL,
    journal_entry_id UUID NOT NULL,
    original_entry JSON NOT NULL,
    corrected_entry JSON NOT NULL,
    correction_reason TEXT,
    batch_id UUID,
    similar_corrected INTEGER DEFAULT 0,
    corrected_by UUID NOT NULL,
    created_at TIMESTAMP
);
```

---

## 📈 Metrics & Monitoring

### Key Metrics
```bash
curl http://localhost:8000/api/review-queue/stats
```

Returnerer:
- **pending:** Antall items som venter
- **auto_approval_rate:** % fakturaer auto-approved
- **escalation_rate:** % fakturaer som krever review
- **average_confidence:** Gjennomsnittlig confidence score

**Målsetninger:**
- Auto-approval rate: >70%
- Escalation rate: <30%
- Average confidence: >75%

---

## 🔄 Integration Points

### 1. Invoice Processing
Når en faktura prosesseres:
```python
# In invoice_processing.py
from app.services.review_queue_manager import process_invoice_for_review

# After AI generates booking suggestion:
result = await process_invoice_for_review(
    db=db,
    invoice_id=invoice.id,
    booking_suggestion=ai_suggestion
)
```

### 2. Chat Integration
Review queue items kan diskuteres via chat:
```python
# Chat can reference review queue items
"Se på review queue item {id} - noe ser rart ut med MVA"
```

---

## 🐛 Known Issues & Future Improvements

### Current Limitations
1. **No user authentication** - resolved_by_user_id settes til None
2. **Pattern matching** - Enkel algoritme, kan forbedres med ML
3. **VAT validation** - Kun sjekker beløp, ikke alle MVA-regler
4. **UI polish** - Grunnleggende design, kan forbedres

### Future Enhancements
1. **ML-based confidence** - Bruke machine learning for bedre prediksjoner
2. **Batch corrections** - Korriger flere items samtidig
3. **Auto-learning improvements** - Mer sofistikert pattern recognition
4. **Mobile support** - Review queue på mobil
5. **Email notifications** - Varsle når items trenger review

---

## 📚 Documentation

### Code Documentation
Alle services har docstrings med:
- Beskrivelse av funksjon
- Args og Returns
- Eksempler

### API Documentation
```bash
# OpenAPI docs
http://localhost:8000/docs

# ReDoc
http://localhost:8000/redoc
```

---

## ✅ Acceptance Criteria

| Krav | Status | Notes |
|------|--------|-------|
| Confidence scoring 0-100% | ✅ | Basert på 5 faktorer |
| Auto-approve >85% | ✅ | Booker direkte til hovedbok |
| Escalate <85% to review queue | ✅ | Med priority og reasoning |
| Review Queue API endpoints | ✅ | GET, approve, correct |
| Corrections learning | ✅ | Pattern creation og auto-correction |
| Frontend UI | ✅ | Liste, detail view, confidence breakdown |
| Demo data (20 invoices) | ✅ | Varierende confidence levels |
| Testing script | ✅ | Automated test suite |

---

## 🎯 Skattefunn AP2 Relevance

Dette Review Queue-systemet er **kritisk** for Skattefunn AP2 fordi:

1. **Tillitsmodell** - Viser at AI ikke bare "gjetter", men har målbare confidence scores
2. **Menneske-i-løkken** - Sikrer at usikre beslutninger alltid sjekkes av mennesker
3. **Læring** - System blir bedre over tid ved å lære fra korreksjoner
4. **Transparens** - Forklarer hvorfor AI er usikker (reasoning)
5. **Kvalitetssikring** - Reduserer feil ved å eskalere usikre tilfeller

**Innovasjon:**
- Automatisk pattern recognition fra corrections
- Batch-korrigering av lignende items
- Confidence breakdown med detaljert forklaring

---

## 📝 Commit Message
```
feat(review-queue): Implement confidence-based escalation system

FASE 2.1 - Review Queue med tillitsbasert eskalering

Backend:
- Confidence scoring service (5 faktorer, 0-100%)
- Corrections learning service med pattern creation
- Review queue manager med auto-escalation
- Enhanced API endpoints med stats og recalculation

Frontend:
- ConfidenceBreakdown component med animasjoner
- Enhanced ReviewQueue UI med filtering
- Confidence visualization og reasoning display

Testing:
- Demo data generator (20 invoices)
- Test script med validation
- Multiple test scenarios

Thresholds:
- >85% = Auto-approve og book til GL
- <85% = Escalate to review queue

Skattefunn AP2: Tillitsmodell med konfidensscoring ✅
```

---

## 👥 Team Notes

**For Backend Team:**
- Confidence algorithm er tunable - juster thresholds i `ConfidenceScorer`
- Patterns kan utvides med mer komplekse matching rules
- Consider caching confidence calculations for performance

**For Frontend Team:**
- ConfidenceBreakdown kan re-uses i andre views
- Consider adding toast notifications for corrections
- Mobile responsive design needs testing

**For QA:**
- Run `test_review_queue.sh` for automated testing
- Manual test scenarios dokumentert over
- Check edge cases: 0% confidence, 100% confidence, duplicate patterns

---

**Implementert av:** Subagent (review-queue-agent)  
**Review:** Klar for Glenn's godkjenning  
**Neste steg:** Integration testing med invoice processing pipeline
