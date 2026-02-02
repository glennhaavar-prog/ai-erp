# AI-AGENT ERP SYSTEM - PROSJEKTBRIEF
**Dato:** 2. februar 2026  
**Kunde:** Glenn Håvar  
**Status:** Planleggingsfase → Implementasjon starter  
**Handoff:** Fra Claude.ai → OpenClawd.ai

---

## 🎯 PROSJEKTMÅL

Bygge et **komplett nytt ERP-system** for det norske markedet som er **AI-agent-first** fremfor GUI-first.

**Hovedkonsept:**
- Tradisjonelt: Menneske → GUI → System → Data
- Vårt system: AI-agent → API → System → Data (menneske = supervisor)

**Målgruppe:**
- Regnskapsbyrå i Norge
- Konkurrere med Tripletex, PowerOffice, etc.
- Differensiering: Bygget FOR AI-agenter fra grunnen av

**Ambisjon:**
- Start: 4 pilotkunder
- Mål: 10,000+ klienter

---

## 📋 GLENN'S SPESIFIKASJONER & BESLUTNINGER

### FASE 1 - Scope (Prioritert)

**Må ha nå:**
1. ✅ Leverandørfakturaer (EHF + PDF)
2. ✅ Utlegg (expense reports)
3. ✅ Review queue for regnskapsførere
4. ✅ Læringssystem (agent lærer fra feedback)

**Kommer senere:**
1. Bankintegrasjon (men må planlegges nå!)
2. Kundefakturaer (via kunde-dashboard)
3. Avstemming (reconciliation)
4. MVA-rapportering til Altinn

### TEKNISKE BESLUTNINGER (Glenn's valg)

**1. Multi-tenant:** JA
- Regnskapsbyrå jobber med flere klienter samtidig
- Kritisk feature

**2. Cloud Platform:** AWS (eu-north-1 - Stockholm/Oslo)
- GDPR-compliant (data i EU)
- Glenn har EC2 instance klar

**3. Kontoplan:** NS 4102 (Standard norsk kontoplan)

**4. Valutaer (Phase 1):**
- NOK (primær)
- EUR
- USD
- DKK
- SEK

**5. Pricing model:** Transaksjonsbasert (fortsatt under utvikling)
- Trolig: Per faktura behandlet
- Estimat: $0.50/faktura

**6. API-valg:** GraphQL
- Valgt for skalerbarhet (10,000+ klienter)
- Real-time subscriptions
- Effektivt for komplekse queries

---

## 🏗️ SYSTEMARKITEKTUR (Oversikt)

### 3 Separate Interfaces:

1. **Agent Workspace**
   - Kun for AI-agenter
   - Administrator kan overstyre
   - Ingen GUI nødvendig (bare APIer)

2. **Accountant Dashboard**
   - Multi-tenant (se flere klienter samtidig)
   - Review queue
   - Agent-kommunikasjon (chat)
   - Godkjenning av AI-forslag
   - "Apply to similar" funksjonalitet

3. **Customer Portal** (senere fase)
   - Kunder ser sin regnskapsstatus
   - Kan sende inn kundefakturaer
   - Vis rapporter

### Agent-strategi:

**Hybrid-modell: "Orchestrator + Specialists"**

```
ORCHESTRATOR AGENT (Main Brain)
├── Ser helhetsbilde
├── Koordinerer andre agenter
├── Lærer mønstre på tvers av moduler
└── Tar overordnede beslutninger
    │
    ├─→ INVOICE AGENT
    │   ├── Parse EHF/PDF
    │   ├── OCR-analyse
    │   ├── Foreslå bokføring
    │   └── Lær leverandørmønstre
    │
    ├─→ BANK AGENT (kommer senere)
    │   ├── Match transaksjoner
    │   ├── Foreslå kontoer
    │   └── Betalingskø
    │
    └─→ RECONCILIATION AGENT (kommer senere)
        ├── Sammenlign datasett
        ├── Finn avvik
        └── Foreslå korrigeringer
```

**Cross-client læring:**
- Agenten lærer fra ALLE klienter i systemet
- Ikke bare én og én klient
- Lagres i `agent_learned_patterns` tabell

---

## 💾 DATABASE (PostgreSQL 16)

**Kjernetabeller (må implementeres først):**

1. **Multi-tenant:**
   - `tenants` - Regnskapsbyrå
   - `clients` - Kunder under hvert byrå
   - `users` - Regnskapsførere

2. **Accounting Core:**
   - `chart_of_accounts` - Kontoplan (NS 4102)
   - `general_ledger` - Hovedbok (immutable!)
   - `general_ledger_lines` - Bilagslinjer (debit/credit)

3. **Vendors & Invoices:**
   - `vendors` - Leverandører
   - `vendor_invoices` - Leverandørfakturaer (EHF + PDF)

4. **Learning & Review:**
   - `review_queue` - Oppgaver som trenger menneskelig review
   - `agent_decisions` - Logger alle AI-beslutninger
   - `human_feedback` - Feedback fra regnskapsførere
   - `agent_learned_patterns` - Cross-client læring (VIKTIG!)
   - `audit_trail` - Fullstendig revisjonslogg (immutable)

5. **Documents:**
   - `documents` - PDFer, XMLer lagret i S3

**Viktige prinsipper:**
- Immutable ledger (ingenting slettes, kun reverseringer)
- Audit trail på ALT
- Spor om endring er gjort av AI eller menneske
- Dobbel bokføring (debit = credit alltid)

---

## 🤖 AI-AGENT WORKFLOW (Detaljert)

### Workflow: EHF-faktura ankommer

```
1. EHF Access Point → Webhook → API
2. API → SQS Queue (enqueue)
3. Worker poller SQS → Orchestrator Agent
4. Orchestrator:
   - Lagrer EHF XML + PDF i S3
   - Oppretter vendor_invoice record
   - Henter vendor history
   - Henter learned patterns
   - Sender til Invoice Agent

5. Invoice Agent:
   - Parser EHF XML
   - Ekstraherer: vendor, beløp, MVA, linjer
   - Analyserer med Claude API
   - Foreslår bokføring (debit/credit)
   - Returnerer confidence score (0-100)

6. Orchestrator beslutter:
   IF confidence >= 85%:
     → Auto-book til general_ledger
     → Notify accountant (low priority)
   ELSE:
     → Send til review_queue
     → Notify accountant (høy prioritet)

7. Logger decision i agent_decisions
```

### Workflow: PDF-faktura lastes opp

```
1. User uploads PDF via web → API
2. API → S3 upload → SQS enqueue
3. Worker:
   - AWS Textract OCR (extract text)
   - Send text til Invoice Agent

4. Invoice Agent (med Claude):
   - Parse OCR text
   - Ekstraher strukturert data
   - Match/create vendor
   - Foreslå bokføring
   - Confidence score

5. Orchestrator → auto-book eller review_queue
```

### Workflow: Human review & learning

```
1. Accountant ser review queue
2. Accountant velger handling:

   a) APPROVE AI suggestion:
      → Create GL entry
      → Mark agent_decision.correct = TRUE
      → Increase pattern confidence

   b) CORRECT AI suggestion:
      → Create GL entry with corrections
      → Mark agent_decision.correct = FALSE
      → Store human_feedback
      
      IF "Apply to similar" checked:
         → Analyze pattern
         → Create agent_learned_patterns entry
         → Apply to ALL pending similar invoices
         → Notify accountant: "Pattern applied to 5 invoices"

   c) CHAT WITH AGENT:
      → Ask for clarification
      → Agent explains reasoning
      → Two-way conversation logged
```

**Læring over tid:**
```
New vendor, no history:
  → Confidence: 60%

After 5 correct bookings:
  → Confidence: 75%

After 10 correct bookings:
  → Confidence: 85% (auto-book threshold!)

After 20 correct bookings:
  → Confidence: 95%

If error occurs:
  → Confidence -10% (temporary)
  → Recovers over time with correct bookings
```

---

## 📊 TECH STACK (Besluttet)

### Backend:
```
Language: Python 3.11
Framework: FastAPI (async, rask)
GraphQL: Strawberry GraphQL (Python-native)
Database: PostgreSQL 16
ORM: SQLAlchemy 2.0 (async)
Caching: Redis 7
Queue: Celery + AWS SQS
AI: Anthropic Claude API (via AWS Bedrock)
OCR: AWS Textract
Storage: AWS S3
```

### Frontend (Accountant Dashboard):
```
Framework: React 18 + TypeScript
Build: Vite
UI: shadcn/ui + Tailwind CSS
State: TanStack Query (React Query)
GraphQL Client: Apollo Client eller urql
Forms: React Hook Form + Zod
PDF Viewer: react-pdf
Charts: Recharts
```

### Infrastructure:
```
Cloud: AWS (eu-north-1 - Stockholm/Oslo)
IaC: Terraform
CI/CD: GitHub Actions
Containers: Docker
Orchestration: AWS ECS Fargate
Monitoring: CloudWatch + Sentry
Logging: CloudWatch Logs (structured JSON)
```

---

## 💰 KOSTNADER

### Pilot (4 klienter, 2-3 måneder):

**AWS Infrastructure:**
```
RDS PostgreSQL (db.t3.micro): $25/mnd
ECS Fargate (2 containers): $50/mnd
S3 Storage (10GB): $0.23/mnd
CloudWatch: $10/mnd
Claude API (800 fakturaer/mnd): $40/mnd
---
Total: ~$130/måned
```

**Utvikling:**
```
Glenn (tid): Din investering
Claude (meg): Gratis via OpenClawd
Developer/Freelancer: $6k-20k (avhengig av approach)
---
Total MVP-kostnad: $6k-20k + AWS $400
```

### Production (10,000 klienter):

**AWS Infrastructure:**
```
Database (RDS + replicas): $2,500/mnd
Compute (ECS Fargate): $5,000/mnd
S3 Storage (5TB): $500/mnd
Claude API (500k fakturaer/mnd): $50,000/mnd
Other (monitoring, etc): $2,000/mnd
---
Total: ~$60,000/måned = $6/klient/måned
```

**Revenue Model (estimert):**
```
Transaksjonsbasert pricing:
  - $0.50 per faktura
  - 50 fakturaer/klient/måned = $25/klient

Margin:
  - Inntekt: $25/klient
  - Kostnad: $6/klient
  - Bruttomargin: $19/klient (76%)

For 10,000 klienter:
  - Månedlig inntekt: $250,000
  - Månedlig kostnad: $60,000
  - Månedlig profitt: $190,000
```

---

## 🎯 SUKSESSKRITERIER

### MVP (4 klienter, 2-3 måneder):
- ✅ 70%+ fakturaer auto-booked
- ✅ 90%+ average confidence score
- ✅ < 2% error rate
- ✅ 30 sekunder processing tid per faktura (vs 3 min manuelt)
- ✅ 8/10 accountant satisfaction
- ✅ Agenten forbedrer seg 5% per måned

### Production (10,000 klienter):
- ✅ 85%+ auto-booking rate
- ✅ 95%+ average confidence
- ✅ < 1% error rate
- ✅ < 5 sekunder processing tid
- ✅ 99.9% uptime
- ✅ API response time: p95 < 200ms

---

## 📝 VIKTIGE NOTATER

### EHF-integrasjon (Pepol):
- Norge bruker EHF (elektronisk faktura)
- Krever aksesspunkt-leverandør (f.eks. Unimicro, Visma)
- XML-format må parses
- Original XML + PDF lagres

### BankID-flow (for Altinn, bank):
```
1. Agent → "Trenger BankID" → Dashboard
2. Accountant → "Jeg er klar" → Agent
3. Agent → Prompt → BankID-request
4. Accountant → BankID approve → Done
```

### Compliance:
- GDPR (data i EU) ✅
- Norwegian Accounting Act
- 5-års dokumentoppbevaring (lovpålagt)
- Revisor-godkjenning (menneske må kunne inspisere alt)

### Sikkerhet:
- JWT authentication
- Role-based access control
- Encrypted credentials (AWS Secrets Manager)
- Audit trail (immutable log)
- No data deletion (kun anonymisering ved GDPR-forespørsel)

---

## 🚀 NESTE STEG (HANDOFF TIL OPENCLAWD)

### Umiddelbart (Uke 1-2):
1. Setup AWS-miljø (RDS, S3, etc.)
2. Initialize database schema
3. Setup FastAPI + GraphQL API
4. Implement auth (JWT)
5. Basic CRUD for clients, vendors

### Uke 3-4:
6. Invoice Agent implementasjon
7. AWS Textract OCR integration
8. Celery task queue
9. S3 document upload

### Uke 5-6:
10. Review queue (backend)
11. Human feedback system
12. Learning engine (agent_learned_patterns)
13. Accountant dashboard (frontend)

### Uke 7-8:
14. Testing
15. Deploy til AWS
16. Pilot med 4 klienter
17. Iterate basert på feedback

---

## 📚 FILER LEVERT

Glenn har fått følgende filer fra Claude (claude.ai):

1. **erp_database_skisse.md**
   - Komplett database schema (PostgreSQL)
   - Alle tabeller med kolonner og relasjoner
   - Multi-currency support
   - AWS deployment detaljer

2. **agent_workflow_and_api.md**
   - Detaljerte agent workflows (sequence diagrams)
   - Komplett GraphQL schema (500+ linjer)
   - Queries, mutations, subscriptions
   - Skaleringsdetaljer for 10,000+ klienter

3. **getting_started_guide.md**
   - Konkrete kodeeksempler (Python + TypeScript)
   - Prosjektstruktur
   - SQLAlchemy models
   - FastAPI setup
   - Invoice Agent kode
   - React komponenter
   - Docker + Terraform

4. **PROJECT_BRIEF.md** (denne filen)
   - Oppsummering av hele prosjektet
   - Glenn's beslutninger og inputs
   - Kontekst for handoff

5. **HANDOFF_TO_OPENCLAWD.md** (neste fil)
   - Spesifikk kontekst for OpenClawd.ai
   - Hvordan komme i gang
   - Forventninger og arbeidsflyt

---

## 🤝 TEAM & ANSVAR

**Glenn Håvar:**
- Produkteier
- Kontakt med pilotkunder
- Validering av regnskapslogikk
- Testing
- Deployment (med hjelp fra Claude/OpenClawd)

**Claude (via OpenClawd.ai):**
- Teknisk arkitekt
- Skriver all kode
- Problemløsning
- Code reviews
- Debugging

**Eventuelt: Freelance Developer (valgfritt):**
- Implementerer kode
- Kjører tester
- Deploy-assistanse
- 20-30 timer/uke

---

## ✅ KONTEKST FOR OPENCLAWD

**Glenn har AWS EC2 instance med Claude Code installert.**

**Forventninger til OpenClawd:**
1. Les alle filene Glenn gir deg
2. Forstå full kontekst av prosjektet
3. Begynn implementasjon av MVP (Phase 1)
4. Kommuniser aktivt med Glenn
5. Spør når du er usikker
6. Lever production-ready kode

**Viktig:** All kode må være:
- Production-ready (ikke bare prototypes)
- Godt dokumentert
- Testet (unit tests + integration tests)
- Sikkert (ingen hardkodede secrets)
- Skalerbart (tenk 10,000 klienter fra dag 1)

---

## 📞 KONTAKTINFO & ARBEIDSFLYT

**Glenn's preferanser:**
- Jobbe tett med AI (deg)
- Daglig oppdateringer
- Spør heller en gang for mye enn for lite
- Validér regnskapslogikk med Glenn før implementering
- Pilotkunder er klare NÅ - må levere fort

**Kommunikasjon:**
- Via OpenClawd.ai interface
- Glenn vil gi kontinuerlig feedback
- Iterativ utvikling (ikke waterfall)

---

## 🎯 KRITISK: Hva som IKKE må glemmes

1. **Immutable ledger** - ingenting slettes fra general_ledger
2. **Audit trail** - alt logges med hvem (AI/human) som gjorde hva
3. **Cross-client learning** - agent_learned_patterns på tvers av alle klienter
4. **Confidence threshold** - justerbar per klient (default: 85%)
5. **"Apply to similar"** - kritisk feature for effektiv læring
6. **BankID-flow** - må planlegges (selv om ikke i MVP)
7. **GDPR compliance** - data i EU, kan slettes på forespørsel
8. **Multi-tenant** - absolutt kritisk (må være med fra dag 1)

---

**END OF PROJECT BRIEF**

Alt er dokumentert. Kontekst er bevart. Klar for handoff! 🚀
