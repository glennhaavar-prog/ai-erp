# Kontali MVP - Kritisk Analyse

**Dato:** 2026-02-05  
**Formål:** Definere minimal viable product som beviser Kontali's unike verdi

---

## Hva Er UNIKT Med Kontali?

### 1. AI som Faktisk Fungerer (Ikke Bare Marketing)
- **Andre systemer:** "AI-powered" = enkel regelmotor
- **Kontali:** Claude Sonnet som faktisk forstår kontekst, lærer, og forbedres

### 2. Learning System
- **Andre:** Statiske regler som må konfigureres manuelt
- **Kontali:** Lærer fra hver correction, deler kunnskap på tvers av klienter

### 3. Confidence-Based Automation
- **Andre:** Alt eller ingenting (100% manual eller 100% auto)
- **Kontali:** 85%+ → auto-book, <85% → review queue

### 4. Norwegian-First
- **Andre:** Generiske ERP-systemer tilpasset Norge
- **Kontali:** Bygget for Norge fra bunnen (EHF, NS 4102, MVA, Altinn)

### 5. Tidsbesparing vs Kostnadsbesparing
- **Andre:** Fokuserer på lavere kostnader
- **Kontali:** Fokuserer på frigjøring av regnskapsførers tid (høyere margin per kunde)

---

## Hva Må MVP Bevise?

### Primary Hypothesis:
> "AI kan bokføre leverandørfakturaer med 85%+ nøyaktighet, og lære over tid, slik at regnskapsførere sparer 70% av tiden på repeterende bokføring."

### Secondary Hypothesis:
> "Regnskapsbyrå vil betale 500-1000 kr/mnd per klient for systemet fordi det lar dem ta flere klienter uten å ansette flere regnskapsførere."

---

## MVP Scope - The Absolute Minimum

### MUST HAVE (Critical Path)

**1. AI Bokføringsflyt (End-to-End)**
- ✅ PDF upload
- ✅ AWS Textract OCR
- ✅ Claude AI analysis
- ✅ NS 4102 account suggestion
- ✅ MVA code detection
- ✅ Confidence scoring

**2. Review Queue**
- ✅ UI for pending reviews
- ✅ Approve button
- ✅ Correct button with feedback
- ✅ Confidence visualization
- ⚠️ Database persistence (CRITICAL - må fikses)

**3. Learning System**
- ⚠️ Corrections stored
- ⚠️ Patterns extracted
- ⚠️ Applied to future invoices
- Status: Backend klar, må testes

**4. Multi-Tenant Foundation**
- ⚠️ Tenant model
- ⚠️ Client model
- ⚠️ User authentication
- Status: Database schema klar, ikke implementert

**5. Core Rapportering**
- ❌ Hovedbok (minimum)
- ❌ Export to Excel
- Status: Planlagt

---

## MVP Feature Matrix

| Feature | Status | MVP? | Rationale |
|---------|--------|------|-----------|
| **AI Invoice Analysis** | ✅ Done | ✅ YES | Core value prop |
| **Review Queue UI** | ✅ Done | ✅ YES | Core workflow |
| **Database Persistence** | ⚠️ 70% | ✅ YES | Can't demo without it |
| **Learning System** | ⚠️ 70% | ✅ YES | Key differentiator |
| **User Login** | ❌ Planned | ✅ YES | Multi-tenant requirement |
| **EHF Auto-Receive** | ✅ Done | ⚠️ NICE | Can start with manual upload |
| **Hovedbok Report** | ❌ Planned | ⚠️ NICE | Need to show results |
| **Saldobalanse** | ❌ Planned | ❌ NO | Can export later |
| **MVA-oppgave** | ❌ Planned | ❌ NO | Phase 2 |
| **Fakturering** | ❌ Planned | ❌ NO | Phase 2 |
| **Bank Integration** | ❌ Ideas | ❌ NO | Phase 3 |

---

## MVP Definition

**"Kontali MVP v1.0"**

A multi-tenant web application where:

1. **Regnskapsbyrå** kan opprette klienter
2. **Regnskapsfører** kan laste opp leverandørfakturaer (PDF)
3. **AI** analyserer og foreslår bokføring (konto + MVA)
4. **Review Queue** viser forslag med confidence score
5. **Regnskapsfører** godkjenner eller korrigerer
6. **System** lagrer corrections og lærer
7. **Rapporten Hovedbok** viser bokførte bilag

**Time to Value:** <5 minutter fra første faktura til bokført bilag

---

## What's NOT in MVP

### Deferred to Phase 2:
- Repeterende fakturaer
- Kunde-fakturering
- Prosjektstyring
- Avstemming
- MVA-innsending
- Periodesperre
- Kunde-portal
- SAF-T import
- PowerOffice migration

### Deferred to Phase 3:
- Bank integration
- Likviditetsprognoser
- AI Support
- B2B Sales CRM
- Fraud detection
- Onboarding automation

---

## Why This MVP Works

### 1. Proves Core Value (AI That Works)
5 fakturaer → AI foreslår → Regnskapsfører godkjenner i sekunder

### 2. Shows Learning
Correction on invoice 1 → Automatically applied to invoice 2

### 3. Measurable Impact
"Before Kontali: 5 min/faktura. After: 30 sec/faktura" = 90% time savings

### 4. Early Adopter Ready
Regnskapsbyrå med 10-50 klienter kan teste med real invoices

### 5. Revenue Validation
Can charge 500 kr/klient/mnd = 5000-25000 kr/mnd for pilot customer

---

## Success Metrics for MVP

**Must Achieve:**
- ✅ 85%+ average confidence score
- ✅ <5% error rate after corrections
- ✅ 80%+ time savings vs manual
- ✅ 1 pilot customer onboarded
- ✅ 100+ invoices processed

**Stretch Goals:**
- 90%+ confidence
- <2% error rate
- 3 pilot customers
- 500+ invoices

---

## Current Status vs MVP

### What We Have (Done Tonight):
- ✅ Backend API (FastAPI)
- ✅ Frontend UI (Next.js)
- ✅ PostgreSQL Database (17 tables)
- ✅ GraphQL API
- ✅ AI Invoice Agent (Claude)
- ✅ AWS Textract OCR
- ✅ Review Queue UI (12 components)
- ✅ Multi-Agent System (backend)
- ✅ Missionboard (project tracking)

**Progress: 70% of MVP**

### What's Missing (Critical):
- ⚠️ Database integration (save invoice → review queue)
- ⚠️ User authentication
- ⚠️ Tenant/Client setup
- ⚠️ Learning system testing
- ❌ Hovedbok report

**Remaining Work: ~20-30 hours**

---

## Risks & Mitigation

### Risk 1: Database Schema Mismatch
**Mitigation:** Fix tonight - align Python models with PostgreSQL schema

### Risk 2: Learning System Not Tested
**Mitigation:** Test with real correction flow this week

### Risk 3: No Authentication
**Mitigation:** Implement JWT auth (4-6 hours work)

### Risk 4: Missing Hovedbok
**Mitigation:** Simple SQL query + Excel export (2 hours)

---

## Recommendation: MVP Roadmap

### Week 1 (This Week):
- ✅ Fix database integration (TONIGHT)
- ✅ Test full flow end-to-end (TONIGHT)
- 🔄 User authentication (2 days)
- 🔄 Tenant/Client setup UI (1 day)

### Week 2:
- 🔄 Hovedbok report
- 🔄 Learning system testing
- 🔄 Bug fixes
- 🔄 Performance optimization

### Week 3:
- 🔄 Pilot customer onboarding
- 🔄 Real invoice processing
- 🔄 Feedback collection
- 🔄 Iteration

### Week 4:
- 🔄 MVP polish
- 🔄 Demo preparation
- 🔄 Go/No-Go decision
- 🔄 Phase 2 planning

---

## Conclusion

**MVP = AI Bokføring + Review Queue + Learning**

Everything else is noise. Focus on proving that AI can:
1. Read invoices correctly
2. Suggest right accounts
3. Learn from corrections
4. Save 80%+ time

Then scale.

---

**Next Step:** Fix database integration TONIGHT and demo full flow tomorrow.
